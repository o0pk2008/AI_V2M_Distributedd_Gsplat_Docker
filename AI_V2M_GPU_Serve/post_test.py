import requests

# 定义post函数
def send_test(gpu_port,project_id,video_path):

    # 向指定IP端口发送post请求
    base_url = f"http://127.0.0.1:{gpu_port}"

    # Test case with project_id and video_path parameters
    data = {'project_id': project_id, 'video_path': video_path}
    endpoint = '/add_task'

    try:
        response = requests.post(f'{base_url}{endpoint}', json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending request: {e}")
        return None

#触发post函数 
send_test(6000,'123','/path/to/video.mp4')