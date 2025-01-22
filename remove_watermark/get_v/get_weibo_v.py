import requests
from bs4 import BeautifulSoup

url = "https://weibo.com/tv/show/1034:5121314302656524?mid=5121327969604247"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}

# 发送请求获取页面内容
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

# 解析页面寻找视频元素和可能的视频源地址
# 此部分需要根据微博页面的具体结构进行调整，以下是一个可能的示例
video_tag = soup.find('video')
if video_tag:
    video_src = video_tag.get('src')
    if video_src:
        # 下载视频
        video_response = requests.get(video_src, headers=headers)
        with open('weibo_video.mp4', 'wb') as f:
            f.write(video_response.content)
    else:
        print("未找到视频源地址")
else:
    print("未找到视频元素")