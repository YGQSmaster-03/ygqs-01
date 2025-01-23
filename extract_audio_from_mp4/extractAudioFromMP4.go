package main

import (
    "bufio"
    "bytes"
    "encoding/binary"
    "fmt"
    "log"
    "os"
    "os/exec"
    "path/filepath"
    "strings"

    "github.com/go-audio/audio"
    "github.com/go-audio/wav"
)

// extractAudioFromMP4 从 MP4 文件中提取音频
func extractAudioFromMP4(mp4Path string, tempAudioPath string) error {
    cmd := exec.Command("ffmpeg", "-i", mp4Path, "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "1", tempAudioPath)
    var out bytes.Buffer
    cmd.Stdout = &out
    cmd.Stderr = &out
    err := cmd.Run()
    if err != nil {
        log.Printf("提取音频时出错: %v, 输出: %s", err, out.String())
        return err
    }
    return nil
}

// readAudioFile 读取音频文件
func readAudioFile(audioPath string) ([]int16, int, error) {
    file, err := os.Open(audioPath)
    if err != nil {
        return nil, 0, err
    }
    defer file.Close()

    decoder := wav.NewDecoder(bufio.NewReader(file))
    if !decoder.IsValidFile() {
        return nil, 0, fmt.Errorf("不是有效的 WAV 文件: %s", audioPath)
    }

    if err := decoder.FullDecode(); err != nil {
        return nil, 0, err
    }

    samples := make([]int16, len(decoder.Data.Floats()))
    for i, f := range decoder.Data.Floats() {
        samples[i] = int16(f * 32767)
    }

    return samples, int(decoder.SampleRate), nil
}

// correlate 互相关函数
func correlate(signal1, signal2 []int16) []float64 {
    n := len(signal1)
    m := len(signal2)
    result := make([]float64, n-m+1)

    for i := 0; i <= n-m; i++ {
        sum := 0.0
        for j := 0; j < m; j++ {
            sum += float64(signal1[i+j]) * float64(signal2[j])
        }
        result[i] = sum
    }

    return result
}

// findAudioSegments 在 MP4 音频中查找 MP3 音频片段的位置
func findAudioSegments(mp4Audio []int16, mp4SR int, mp3Audio []int16, mp3SR int, threshold float64) [][2]float64 {
    if mp4SR != mp3SR {
        log.Println("采样率不一致，暂不支持重采样")
        return nil
    }

    corr := correlate(mp4Audio, mp3Audio)
    maxCorr := 0.0
    for _, c := range corr {
        if c > maxCorr {
            maxCorr = c
        }
    }

    segments := [][2]float64{}
    for i, c := range corr {
        if c >= maxCorr*threshold {
            startTime := float64(i) / float64(mp4SR)
            endTime := startTime + float64(len(mp3Audio))/float64(mp4SR)
            segments = append(segments, [2]float64{startTime, endTime})
        }
    }

    return segments
}

// findSimilarSegments 查找文件夹中所有 MP4 文件中包含 MP3 音频片段的部分
func findSimilarSegments(folderPath string, mp3Path string) {
    mp3Audio, mp3SR, err := readAudioFile(mp3Path)
    if err != nil {
        log.Printf("读取 MP3 文件时出错: %v", err)
        return
    }

    err = filepath.Walk(folderPath, func(path string, info os.FileInfo, err error) error {
        if err != nil {
            return err
        }
        if !info.IsDir() && strings.HasSuffix(strings.ToLower(info.Name()), ".mp4") {
            tempAudioPath := "temp_audio.wav"
            if err := extractAudioFromMP4(path, tempAudioPath); err != nil {
                return nil
            }

            mp4Audio, mp4SR, err := readAudioFile(tempAudioPath)
            if err != nil {
                log.Printf("读取 MP4 音频时出错: %v", err)
                os.Remove(tempAudioPath)
                return nil
            }

            segments := findAudioSegments(mp4Audio, mp4SR, mp3Audio, mp3SR, 0.8)
            if len(segments) > 0 {
                fmt.Printf("文件名: %s\n", info.Name())
                fmt.Printf("出现次数: %d\n", len(segments))
                for i, segment := range segments {
                    fmt.Printf("第 %d 次出现时间区间: %.2fs - %.2fs\n", i+1, segment[0], segment[1])
                }
            } else {
                fmt.Printf("文件名: %s, 未找到匹配的音频片段。\n", info.Name())
            }

            os.Remove(tempAudioPath)
        }
        return nil
    })

    if err != nil {
        log.Printf("遍历文件夹时出错: %v", err)
    }
}

func main() {
    folderPath := "./"   // MP4 所在的文件夹
    mp3Path := "123.MP3" // 提供的 MP3 片段采样
    findSimilarSegments(folderPath, mp3Path)
}
