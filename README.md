## Nc2server
#### 一个小小尝试

目前计划
* python web 服务器端
* go 客户端
* 反弹shell 直连shell
* 敏感信息收集

### 笔记

go后端接受明文输入，返回base64 ，由前端处理
输入明文前端处理为base64传输到后端解码之后，再传输到客户端处理
