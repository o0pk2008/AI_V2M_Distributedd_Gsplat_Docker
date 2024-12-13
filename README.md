# AI_V2M_Distributedd_Gsplat_Docker
物件扫描Docker版本

# 环境配置

## Docker 环境启动
```bash
docker run --gpus all -it \
    -v E:\Python\AI_V2M_Distributedd_Gsplat_Docker:/source/object_server \
    -p 5201:5201 nerfstudio:v5 /bin/bash
```

## 配置虚拟环境
```bash
conda activate nerfstudio
```

## 服务启动

### 1. 进入项目目录
```bash
cd /source/object_server/AI_V2M_GPU_Serve
```

### 2. 启动建模服务
```bash
python3 modeling_serve.py --port 5201
```

## 注意事项
- **确保已安装 NVIDIA Docker 支持**
- **确保本地目录映射路径正确**
- **默认计算节点服务端口为 5201**
