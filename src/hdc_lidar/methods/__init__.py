from hdc_lidar.methods.autoencoder import AutoencoderMethod
from hdc_lidar.methods.binary_hash import BinaryHashMethod
from hdc_lidar.methods.hybrid_hdc import HybridHDCMethod
from hdc_lidar.methods.pca import PCAMethod
from hdc_lidar.methods.pure_hdc import PureHDCMethod
from hdc_lidar.methods.quantization import QuantizedMethod


def build_method(name: str, budget_bytes: int, seed: int = 0, **kwargs):
    name = name.lower()
    if name in {"quantized", "quant8", "quantization"}:
        return QuantizedMethod(budget_bytes, seed=seed, n_bits=kwargs.get("n_bits", 8))
    if name in {"raw", "raw_float32"}:
        return QuantizedMethod(budget_bytes, seed=seed, raw_float32=True)
    if name == "pca":
        return PCAMethod(budget_bytes, seed=seed, coeff_dtype=kwargs.get("coeff_dtype", "float32"))
    if name in {"autoencoder", "ae"}:
        return AutoencoderMethod(budget_bytes, seed=seed)
    if name in {"binary_hash", "hashing"}:
        return BinaryHashMethod(
            budget_bytes, seed=seed, dimension=kwargs.get("dimension")
        )
    if name in {"pure_hdc", "hdc"}:
        return PureHDCMethod(
            budget_bytes,
            seed=seed,
            dimension=kwargs.get("dimension", 4096),
            n_levels=kwargs.get("n_levels", 32),
            level_mode=kwargs.get("level_mode", "locality"),
            similarity=kwargs.get("similarity", "cosine"),
            region_size=kwargs.get("region_size", 1),
        )
    if name in {"hybrid_hdc", "hybrid"}:
        return HybridHDCMethod(
            budget_bytes,
            seed=seed,
            dimension=kwargs.get("dimension", 4096),
            mode=kwargs.get("mode", "task"),
        )
    raise ValueError(f"Unknown method {name}")
