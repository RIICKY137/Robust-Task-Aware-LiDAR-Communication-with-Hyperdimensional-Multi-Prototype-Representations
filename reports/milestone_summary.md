# 阶段性总结 — HDC 任务感知 LiDAR 通信

**日期：** 2026-08-30  
**工作点：** 每帧 **128 字节**，HDC 维数 `D=1024`，接收端每类 **k=16** 质心，无效光束 **skip**（或 DROP）  
**本文不是曲线源。** 数字来自 `results/raw/*.jsonl`，由 `scripts/aggregate_results.py` 写入分阶段报告。不要手改那些表。

---

## 1. 问题与成功标准

带宽受限、信道不稳定时，机器人要把 2D LiDAR 扫描变成可分类的地点类型。接收端 **不重建点云**，只从传输表示做 5 类地点分类：`corridor`、`room`、`doorway`、`open_area`、`cluttered_area`。

Brief 的成功标准不是「HDC 全面赢」，而是画出 **工作区**（带宽 × 噪声 × 适应代价）：

| 代号 | 含义 |
|---|---|
| A | 相近精度、更少字节 |
| B | BER / burst / 丢包下掉得更慢 |
| C | 环境偏移后，few-shot 更便宜 |
| D | 明确标出失败区 |

对照方法共享同一字节预算：8-bit PCM、PCA、随机二值 hashing、纯 HDC、自编码器、hybrid neural-HDC。载荷是 **每帧一个超向量**；`k` 是接收端每类质心数，不是把扫描切成 k 段分别发送。

---

## 2. 做到哪一步

原计划 Stage 0→5 + Stage 8。仿真矩阵已跑完；真实 2D 做到作者标签上的 Stage 1/2/3。硬件 OTA 仍未做。

| 阶段 | 内容 | 仿真 `sim_indoor_v1` | 真实数据 |
|---|---|---|---|
| 0 | 数据与划分 | 5315 帧，楼层 OOD | Semantic2D（推导标签）；LidarDataFrames（作者标签，411 帧） |
| 1 | 精度–带宽 | k=1 首轮 + k=16 重做 | 仅 128 B |
| 2 | BER / burst / 丢包 | 首轮 + 128 B 重做 | LidarDataFrames：BER 0 / 0.05 / 0.10 |
| 3 | 传感器空洞 / 尺度 / 楼层 OOD | 首轮 fill + skip/DROP 修正 | LidarDataFrames：dropout / scale；**无楼栋 OOD** |
| 4 | 偏移后 10/50/100-shot | 512 B 与 128 B | **未做**（holdout 太小，且不是 building shift） |
| 5 | hybrid neural-HDC | 完成 | 未做 |
| 8 | 电台 | 未编码 BPSK/QPSK + AWGN/Rayleigh **仿真** | **无 OTA**（本环境无 SDR） |

交互实验室：`python scripts/serve_lab.py 43187`，可切换 `sim_indoor_v1` / `semantic2d_v1` / `lidardataframes_v1`。

---

## 3. 三条数据线（不要混在一起读）

### 3.1 室内仿真 `sim_indoor_v1`

标签来自位姿落在平面图区域上，扫描几何与标签对齐。5315 帧；`test_id` 同楼轨迹留出；`test_ood` 是另一张平面图。这是编号实验的主矩阵。

### 3.2 Semantic2D `semantic2d_v1`

真实 Hokuyo 扫描（Zenodo Semantic2D）。作者只有点级物体标签，**没有走廊/房间地点标注**。地点由几何启发式推出（近门→doorway，家具→cluttered 等）。8265 帧（stride 10）；OOD 为 lobby + eng_9th。类别极不均衡（room 38%，doorway 32%，corridor 6%）。

**精度是与启发式的一致率，不是人类地点判断。** ID ~0.50 不能当成「真实 LiDAR 在 128 B 上不可分」。

### 3.3 LidarDataFrames `lidardataframes_v1`

Kaggle FourClassDS：RPLiDAR A1，**作者** 四类地点（hall → `open_area`），无 `cluttered_area`。411 帧。CSV 无楼栋 id，`test_ood` 是分层 i.i.d. 留出，**不是楼层偏移**。N 小（测试约 80 帧）。作者已填过部分缺失回波。

---

## 4. 对照 A / B / C / D

下列数字除非注明，均为仿真、`test_id`、多种子均值。完整表见对应 `reports/stage*.md`。

### A — 更少字节

首轮 **k=1** 不是压缩胜利：干净信道上精度卡在 ~0.73，hashing 在 512 B 已是 ~0.92。

**k=16** 在 128 B（`D=1024`）就饱和：ID ~0.95，OOD ~0.84。hashing 要到 2048 B 才在 ID 上接近；OOD 仍停在 ~0.58–0.63。8-bit PCM 在 ~188 B 饱和，多给字节用不上。线性头 ID 随字节上升（0.95→0.98），OOD 全程低于 k=16。

**结论：** Outcome A 对 k=1 失败，对 k=16 在仿真上成立（128 B 对齐 hashing 的 2048 B ID，并保住 OOD）。不能推广成「任意 k 的 HDC 都更省带宽」。

### B — 噪声掉得更慢

128 B 上 k=16 **BER 平坦**：ID ~0.95，BER 0→0.10 几乎不动。k=1 也平坦，但停在 ~0.73。线性头在 128 B **不是全息的**（~0.95→~0.86）；512 B 时才接近平坦。hashing 128 B：~0.86→~0.68。PCM：~0.74→~0.31。

- 32 B 分组、PLR 0.20：k=16 仍 ~0.95。
- 1024-bit 码上 **128-bit burst**：k=16 不动；**512-bit burst（半个码）**：所有方法掉到随机水平。

未编码电台（仿真，非空口）：BPSK-AWGN 与 matched BER 重合，说明 i.i.d. BER 没有夸大 k=16。Block Rayleigh 在 Eb/N0 = −2 dB 经验 BER ~0.19，k=16 ID 仍 ~0.95。线性头吃亏的是 **成簇误码**，不只是平均 BER。

**结论：** Outcome B 在 128 B、k=16、随机/短突发/分组丢失上成立。半码长突发是失败区（D）。

### C — 便宜的 few-shot

仅仿真、楼层 OOD。128 B：适应前 OOD 为 k=16 0.841 / 线性 0.794 / k=1 0.699。100 shot 后 k=16 → 0.910（~80 ms 质心加减），线性 → 0.898（~5 s 重训）。k=1 到 0.751，不是工作点。k=16 遗忘小（100 shot 时 ID 掉 ~0.008）。

512 B 时线性头在 100 shot 能追上 k=16；**128 B 追不上**。

**结论：** Outcome C 在仿真楼层偏移、128 B 上成立（更便宜，且未被线性头反超）。真实作者标签 + 楼栋偏移上 **尚未验证**。

### D — 已标出的失败区

| 失败区 | 现象 |
|---|---|
| k=1 当压缩机 | 任何预算 ID ~0.73 |
| 128 B 线性头 + 随机 BER / 成簇衰落 | 干净时接近 k=16，噪声下掉 |
| 512-bit burst on 1024-bit 码 | 全体崩溃 |
| 扇区空洞 + max-range **fill** | 假开口：仿真 30% 扇区 ID ~0.39 |
| Semantic2D 推导标签当「真实地点精度」 | ID ~0.50，OOD ~0.35（接近多数类） |
| 把 LidarDataFrames 的 `test_ood` 当成楼层 OOD | 只是 i.i.d. 留出 |

扇区空洞在改成 **skip / DROP** 后不再是分类器失败：仿真 30% 扇区 ID fill 0.39 → skip/DROP ~0.90。真实 LidarDataFrames 上同样：fill 0.67，skip 0.84，DROP 0.90。

---

## 5. 工作区（当前读法）

**在仿真 2D、地点标签与几何对齐、每帧一个 HV、k=16、skip/DROP 编码时：**

- **128 B 已够用**（再加字节几乎不抬 k=16）。
- **随机 BER 到 0.10、PLR 0.20、128-bit burst、未编码 BPSK AWGN / 短相干 Rayleigh** 仍接近干净精度。
- **随机丢束** 可扛；**成片扇区缺失** 必须标成无效，不能填成最远距。
- **楼层偏移** 后，质心 10/50/100-shot 能抬 OOD，且比重训线性头便宜。

**线性头** 在干净、大预算、i.i.d. 真实小样本上可以持平或略高，但在 128 B 全息噪声、成簇误码、扇区空洞上更弱。不要用「干净精度」代替工作区。

**真实扫描：** 作者地点标签（LidarDataFrames）上，干净与 BER 平坦回到 ~0.97，PCM 仍悬崖。推导标签（Semantic2D）天花板低，是标签定义问题，不是编码器在真实波形上坏了。两者都不能代替带楼栋标签的大规模 OOD。

---

## 6. 真实数据：两条线必须分开写

| | Semantic2D | LidarDataFrames |
|---|---|---|
| 扫描 | 真 | 真 |
| 地点标签 | 启发式 | 作者 |
| 规模 | 8265 | 411 |
| 楼栋 OOD | 有（lobby + 9th） | 无 |
| 128 B k=16 ID | ~0.50，BER 平坦 | ~0.97，BER 平坦 |
| 128 B 线性 ID | 0.45→0.37（BER 0.10） | ~0.98，也平坦 |
| Stage 3 dropout | 未做 | skip/DROP 优于 fill |

LidarDataFrames 上 k=1 与 k=16 都在天花板附近，**不能** 用来证明 k=16 优于线性头；只能说明：真实平面扫描 + 作者地点标签时，128 B 分类是可行的，PCM 在 BER 下仍垮。

---

## 7. 明确没有验证的

- 空口电台、真机 SDR、真实调制损伤（功放、同步、邻频）。
- 带作者地点标签的 **楼栋/楼层偏移** few-shot（Stage 4 在真实数据上）。
- 实时机器人闭环、3D LiDAR、多传感器。
- Semantic2D 若重标成人类地点，精度会不会回到 ~0.95（未做 gold test）。
- k=16 在真实数据上相对线性头的优势（小样本上两者都顶格）。

---

## 8. 原计划还剩什么

本环境能诚实做完的软件编号已经收口。Brief 里仍开着的是：

1. **Stage 8 硬件电台** — 需要 SDR / 实采。
2. **真实数据上的 Stage 4** — 需要作者地点标签 **且** 有 session/楼栋 id，holdout 还要够 10/50/100 shot/类。

给 Semantic2D 打 gold、再搜更大语料，是诊断补丁，不是原来的编号步骤。

---

## 9. 怎么读仓库

| 想看什么 | 去哪 |
|---|---|
| 本总结 | `reports/milestone_summary.md` |
| 由 JSONL 生成的 RQ 总表 | `reports/final_report.md` |
| 仿真带宽 / BER / dropout / few-shot / 电台 | `reports/stage1_k16_bandwidth.md` 等 `stage*_k16_*.md` |
| 真实扫描 | `reports/stage0_semantic2d.md`、`stage0_lidardataframes.md`、`stage3_k16_lidardataframes_sensor.md` |
| 原始数字 | `results/raw/*.jsonl`（不要覆盖首轮仿真文件） |
| 曲线 | `results/figures/` |
| 冻结划分 | `data/splits/` |
| 实验室 | `python scripts/serve_lab.py 43187` |

复现：见仓库根目录 `README.md` 中的阶段脚本顺序。处理数据在 `data/processed/`（gitignore）；仿真用 `python scripts/prepare_data.py`，LidarDataFrames 需要 `data/raw/lidardataframes/FourClassDS.csv`。
