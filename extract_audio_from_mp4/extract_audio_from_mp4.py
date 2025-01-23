import os
import librosa
import numpy as np
from moviepy.editor import VideoFileClip
from scipy.signal import correlate
import contextlib

"""
@此文件目的是：查找MP4中是否含有 提供的MP3音频片段  匹配几次，起止时间
"""
def extract_audio_from_mp4(mp4_path):
    """
    从 MP4 文件中提取音频
    :param mp4_path: MP4 文件路径
    :return: 音频信号和采样率
    """
    clip = VideoFileClip(mp4_path)
    audio = clip.audio
    with open(os.devnull, 'w') as fnull, contextlib.redirect_stdout(fnull), contextlib.redirect_stderr(fnull):
        audio.write_audiofile("temp_audio.wav")
    y, sr = librosa.load("temp_audio.wav")
    os.remove("temp_audio.wav")
    return y, sr

def find_audio_segments(mp4_audio, mp4_sr, mp3_audio, mp3_sr, downsample_rate=4, threshold=0.8):
    """
    在 MP4 音频中查找所有 MP3 音频片段的位置
    :param mp4_audio: MP4 音频信号
    :param mp4_sr: MP4 音频采样率
    :param mp3_audio: MP3 音频信号
    :param mp3_sr: MP3 音频采样率
    :param downsample_rate: 下采样率
    :param threshold: 匹配阈值
    :return: 匹配的起始和结束时间列表（秒）
    """
    # 调整 MP3 音频采样率与 MP4 音频一致
    mp3_audio_resampled = librosa.resample(mp3_audio, orig_sr=mp3_sr, target_sr=mp4_sr)

    # 下采样以减少计算量
    mp4_audio_downsampled = mp4_audio[::downsample_rate]
    mp3_audio_downsampled = mp3_audio_resampled[::downsample_rate]

    # 使用互相关进行匹配
    correlation = correlate(mp4_audio_downsampled, mp3_audio_downsampled, mode='valid')
    max_corr = np.max(correlation)
    segments = []
    start_index = 0
    while True:
        current_correlation = correlation[start_index:]
        if len(current_correlation) == 0:
            break
        max_index = np.argmax(current_correlation) + start_index
        if correlation[max_index] < max_corr * threshold:
            break

        # 计算实际的起始和结束索引
        actual_start_index = max_index * downsample_rate
        actual_end_index = actual_start_index + len(mp3_audio_resampled)

        # 转换为时间（秒）
        start_time = actual_start_index / mp4_sr
        end_time = actual_end_index / mp4_sr
        segments.append((start_time, end_time))

        # 跳过已经匹配的部分继续查找
        start_index = max_index + len(mp3_audio_downsampled)

    return segments

def find_similar_segments(folder_path, mp3_path):
    """
    查找文件夹中所有 MP4 文件中包含 MP3 音频片段的部分
    :param folder_path: 文件夹路径
    :param mp3_path: MP3 文件路径
    """
    mp3_audio, mp3_sr = librosa.load(mp3_path)
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.mp4'):
                mp4_path = os.path.join(root, file)
                mp4_audio, mp4_sr = extract_audio_from_mp4(mp4_path)
                segments = find_audio_segments(mp4_audio, mp4_sr, mp3_audio, mp3_sr)
                if segments:
                    print(f"文件名: {file}")
                    print(f"出现次数: {len(segments)}")
                    for i, (start_time, end_time) in enumerate(segments, start=1):
                        print(f"第 {i} 次出现时间区间: {start_time:.2f}s - {end_time:.2f}s")
                else:
                    print(f"文件名: {file}, 未找到匹配的音频片段。")

# 示例使用
folder_path = './'
mp3_path = '123.MP3'
find_similar_segments(folder_path, mp3_path)
