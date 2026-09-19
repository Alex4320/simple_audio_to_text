from functools import lru_cache

import imageio_ffmpeg


@lru_cache(maxsize=1)
def ffmpeg_executable() -> str:
    return imageio_ffmpeg.get_ffmpeg_exe()
