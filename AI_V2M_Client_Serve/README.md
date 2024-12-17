# 物件扫描服务端 + 客户端

## quick Start

```bash
# 激活名为 FLASK 的python虚拟环境
conda activate FLASK

# 运行项目(正式环境)
python main.js

# 运行项目（开发环境）
env=dev python main.js

# 运行项目（测试环境，暂时没有配置）
env=test python main.js
```

说明：不同的环境对应不同的配置文件：
```
config.toml
config_dev.toml
config_test.toml
```

如果要新增环境，添加新的toml配置文件后，在`app\config.py`文件中增加配置文件读取判断。
