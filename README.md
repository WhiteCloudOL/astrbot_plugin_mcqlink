# MCQLink For Astrbot  

> AstrBotQQ端插件：https://github.com/WhiteCloudOL/astrbot_plugin_mcqlink  
> Minecraft Bukkit/Spigot/Paper插件：https://github.com/WhiteCloudOL/MCQLinkPlugin  

# 介绍/Intro
## 它能做什么？
1. 建立websocket连接  
2. 收发事件消息，处理消息逻辑，转化为可读语言  

## 如何使用？
不可单独使用，此为websocket服务端，需要连接至websocket客户端  
搭配用于QQ与Minecraft通讯的Bukkit插件可见 https://github.com/WhiteCloudOL/MCQLinkPlugin  
理论上你也可以参照此消息格式独立开发设计一个模组/插件用于连接此服务端  

## 安装/Install  

### 自动安装
Astrbot插件市场搜索 mcqlink 即可自动下载  

### 手动安装
1. 方式一：直接下载：  
点击右上角`<>Code`->`Download Zip`下载压缩包  
打开`Astrbot/data/plugins/`下载本仓库文件，创建`astrbot_plugins_mcqlink`目录，解压所有文件到此目录即可  
2. 方式二：Git Clone方法  
请确保系统已经安装git  
打开目录`Astrbot/data/plugins/`，在此目录下启动终端执行:  
```bash
# 全球/海外/港澳台
git clone https://github.com/WhiteCloudOL/astrbot_plugin_mcqlink.git  

# 大陆地区#1
git clone https://gh-proxy.com/https://github.com/WhiteCloudOL/astrbot_plugin_mcqlink.git

# 大陆地区#2
git clone https://cdn.gh-proxy.com/https://github.com/WhiteCloudOL/astrbot_plugin_mcqlink.git
```

# 配置/Configure
请在 `Astrbot控制台-插件-mcqlink-插件配置` 中：  
1. 配置server_ip(默认`0.0.0.0`，监听所有)  
2. 配置server_port(默认`6215`)  
3. 配置token(默认`mcqlink`)，**建议更改为强密码！！**  
4. 配置enable_group(默认为空)，**必须配置**，否则无法收发信息！！！  


# 支持

[帮助文档](https://astrbot.app)
