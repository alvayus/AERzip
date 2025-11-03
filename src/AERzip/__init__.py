__version__ = "1.0.0"

from .CompressedFileHeader import CompressedFileHeader
from .functions import(saveCompressedFile, loadCompressedFile)

__all__ = ["CompressedFileHeader", "saveCompressedFile", "loadCompressedFile"]
