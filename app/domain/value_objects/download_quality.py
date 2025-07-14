from enum import Enum


class DownloadQuality(Enum):
    """Qualidades disponíveis para download"""
    
    BEST = "best"  # Melhor qualidade disponível
    WORST = "worst"  # Pior qualidade disponível
    BEST_VIDEO = "bv+ba"  # Melhor vídeo + melhor áudio
    BEST_VIDEO_ONLY = "bv"  # Apenas melhor vídeo
    BEST_AUDIO_ONLY = "ba"  # Apenas melhor áudio
    HD_1080 = "1080p"
    HD_720 = "720p"
    HD_480 = "480p"
    HD_360 = "360p"
    HD_240 = "240p"
    HD_144 = "144p" 