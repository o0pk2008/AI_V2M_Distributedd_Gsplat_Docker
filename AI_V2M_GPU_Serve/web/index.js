// 服务器IP地址
const ServerIP = "http://127.0.0.1";

// 统计数据
let OnlineServerNum = 0;
let Calculating = 0;
let task_num = 0;
let taskEnd_num = 0;

// 在页面加载完成后执行的JavaScript代码
document.addEventListener('DOMContentLoaded', async function () {
    LoopEvent();
    getGpusystem_info();
    // 基本信息轮询事件
    setInterval(LoopEvent, 1000);
    // 硬件信息轮询事件
    setInterval(getGpusystem_info, 10000);
});

// 轮询事件
async function LoopEvent() {
    await getGpuServers();
    await getTaskNum();
    await getTaskEndNum();
}

// 获取GPU服务器信息的函数
async function getGpuServers() {
    try {
        const response = await fetch('/get_gpu_servers');
        const data = await response.json();

        // 重置统计数据
        OnlineServerNum = 0;
        Calculating = 0;

        if (data.hasOwnProperty('gpu_servers')) {
            const gpuServers = data.gpu_servers;
            gpuServers.forEach(server => {
                SetGPU_State(server.name, server.status);
            });

            // 更新在线服务器数量和计算中数量
            document.getElementById('Online-Server').innerHTML = OnlineServerNum;
            document.getElementById('Calculating').innerHTML = Calculating;
        } else {
            console.error('Unexpected response structure');
        }
    } catch (error) {
        console.error('Error fetching GPU server information:', error);
    }
}

// 获取GPU待计算任务总数
async function getTaskNum() {
    try {
        const response = await fetch('/get_task_num');
        const data = await response.json();

        if (data.hasOwnProperty('task_num')) {
            task_num = data.task_num;
            document.getElementById('Task-Queue').innerHTML = task_num;
        } else {
            console.error('Unexpected response structure');
        }
    } catch (error) {
        console.error('Error fetching GPU server information:', error);
    }
}

// 获取GPU已完成任务数量
async function getTaskEndNum() {
    try {
        const response = await fetch('/get_taskEnd_num');
        const data = await response.json();

        if (data.hasOwnProperty('taskEnd_num')) {
            taskEnd_num = data.taskEnd_num;
            document.getElementById('Total-Completed').innerHTML = taskEnd_num;
        } else {
            console.error('Unexpected response structure');
        }
    } catch (error) {
        console.error('Error fetching GPU server information:', error);
    }
}

// 设置GPU在线状态
function SetGPU_State(name, status) {
    let containerDiv = document.getElementById(name);
    let elementsWithClass = containerDiv.getElementsByClassName('status');
    let elementsWithClass2 = containerDiv.getElementsByClassName('status1');

    let statusElement = elementsWithClass[0];
    let statusElementText = elementsWithClass2[0];

    switch (status) {
        case 'idle':
            if (statusElementText) {
                statusElementText.innerHTML = 'idle';
                OnlineServerNum++;
            }
            if (statusElement) {
                statusElement.style.backgroundColor = '#99e948';
            }
            break;

        case 'busy':
            if (statusElementText) {
                statusElementText.innerHTML = 'busy';
                OnlineServerNum++;
                Calculating++;
            }
            if (statusElement) {
                statusElement.style.backgroundColor = '#eabe4c';
            }
            break;

        case 'offline':
            if (statusElementText) {
                statusElementText.innerHTML = 'offline';
            }
            if (statusElement) {
                statusElement.style.backgroundColor = '#a0a0a0';
            }
            break;
    }
}

// 获取并设置GPU硬件信息
async function getGpusystem_info() {
    try {
        const response = await fetch('/get_gpu_servers');
        const data = await response.json();

        if (data.hasOwnProperty('gpu_servers')) {
            const gpuServers = data.gpu_servers;
            gpuServers.forEach(server => {
                SetGPU_system_info(server.name, server.status);
            });
        } else {
            console.error('Unexpected response structure');
        }
    } catch (error) {
        console.error('Error fetching GPU server information:', error);
    }
}

// 设置GPU硬件信息
function SetGPU_system_info(name, status) {
    let containerDiv = document.getElementById(name);
    if (status !== 'offline') {
        switch (name) {
            case 'GPU1':
                get_system_info(containerDiv, 5201);
                break;

            case 'GPU2':
                get_system_info(containerDiv, 5202);
                break;

            case 'GPU3':
                get_system_info(containerDiv, 5203);
                break;
        }
    }
}

// 获取GPU设备硬件信息
async function get_system_info(containerDiv, port) {
    const timeoutPromise = new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 10000));

    try {
        const response = await Promise.race([fetch(`${ServerIP}:${port}/get_system_info`), timeoutPromise]);
        const data = await response.json();

        if (data.hasOwnProperty('ip')) {
            // 对data数据进行解构赋值
            const { platform, version, ip, memory_info, uptime, network_usage, disk_usage, download_speed, upload_speed, cpu, disk, memory } = data;
            // 使用模板字符串语法
            // containerDiv.querySelector('.Windows').innerHTML = `${platform} ${version}`;
            containerDiv.querySelector('.Windows').innerHTML = `${platform}`;
            containerDiv.querySelector('.ip').innerHTML = ip;
            containerDiv.querySelector('.memory_info').innerHTML = memory_info;
            containerDiv.querySelector('.uptime').innerHTML = uptime;
            containerDiv.querySelector('.network_usage').innerHTML = network_usage;
            containerDiv.querySelector('.disk_usage').innerHTML = disk_usage;
            containerDiv.querySelector('.download_speed').innerHTML = `${download_speed.toFixed(2)}Kbps`;
            containerDiv.querySelector('.upload_speed').innerHTML = `${upload_speed.toFixed(2)}Kbps`;

            let cpuElement = containerDiv.querySelector('.cpu');
            let elementsnetprogressCPU = containerDiv.getElementsByClassName('progressCPU');
            let diskElement = containerDiv.querySelector('.disk');
            let elementsnetprogressDISK = containerDiv.getElementsByClassName('progressDISK');
            let ramElement = containerDiv.querySelector('.ram');
            let elementsnetprogressRAM = containerDiv.getElementsByClassName('progressRAM');

            // nextElementSibling访问元素的下一个同级元素的属性
            cpuElement.innerHTML = `${Math.min(cpu * 10, 100)}%`;
            elementsnetprogressCPU[0].value = Math.min(cpu * 10, 100);

            diskElement.innerHTML = `${disk}%`;
            elementsnetprogressDISK[0].value = disk;

            ramElement.innerHTML = `${memory}%`;
            elementsnetprogressRAM[0].value = memory;
        }
    } catch (error) {
        console.error('Fetch error:', error);
    }
}

/*************************************************************************************
/*** 优化前的代码备份 20240206
/*************************************************************************************
// 服务器IP地址
var ServerIP = "http://127.0.0.1";

// 服务器硬件参数
var platform;
var version;
var ip;
var memory_info;
var uptime;
var network_usage;
var disk_usage;
var download_speed;
var upload_speed;
var cpu;
var disk;
var memory;

// 在页面加载完成后执行的JavaScript代码
document.addEventListener('DOMContentLoaded', function () {
    LoopEvent();
    getGpusystem_info();
    // 基本信息轮询事件
    setInterval(LoopEvent, 1000);
    // 硬件信息轮询事件
    setInterval(getGpusystem_info, 10000);
});

// 统计数据
var OnlineServerNum,task_num,Calculating,taskEnd_num = 0;

// 轮询事件
function LoopEvent(){
    getGpuServers();
    getTaskNum();
    getTaskEndNum();
}

// 获取GPU服务器信息的函数
async function getGpuServers() {
    try {
        const response = await fetch('/get_gpu_servers');
        const data = await response.json();

        // 统计数据
        OnlineServerNum = 0;
        Calculating = 0;

        // Check if the response has the expected structure
        if (data.hasOwnProperty('gpu_servers')) {
            const gpuServers = data.gpu_servers;
            // Loop through each GPU server and display information
            gpuServers.forEach(server => {
                // `ID: ${server.id}, Name: ${server.name}, Port: ${server.port}, Status: ${server.status}`;
                SetGPU_State(server.name,server.status);
            });
            
            // 统计服务器上线数量
            var elementsOnlineServer = document.getElementById('Online-Server');
            elementsOnlineServer.innerHTML = OnlineServerNum;
            var elementsCalculating = document.getElementById('Calculating');
            elementsCalculating.innerHTML = Calculating;
        } else {
            console.error('Unexpected response structure');
        }
    } catch (error) {
        console.error('Error fetching GPU server information:', error);
    }
}

// 获取GPU待计算任务总数
async function getTaskNum() {
    try {
        const response = await fetch('/get_task_num');
        const data = await response.json();

        // Check if the response has the expected structure
        if (data.hasOwnProperty('task_num')) {
            task_num = data.task_num;
            // 统计服务器上线数量
            var elementsTaskQueue = document.getElementById('Task-Queue');
            elementsTaskQueue.innerHTML = task_num;
        } else {
            console.error('Unexpected response structure');
        }
    } catch (error) {
        console.error('Error fetching GPU server information:', error);
    }
}

// 获取GPU已完成任务数量
async function getTaskEndNum() {
    try {
        const response = await fetch('/get_taskEnd_num');
        const data = await response.json();

        // Check if the response has the expected structure
        if (data.hasOwnProperty('taskEnd_num')) {
            taskEnd_num = data.taskEnd_num;
            // 统计服务器上线数量
            var elementsTotalCompleted = document.getElementById('Total-Completed');
            elementsTotalCompleted.innerHTML = taskEnd_num;
        } else {
            console.error('Unexpected response structure');
        }
    } catch (error) {
        console.error('Error fetching GPU server information:', error);
    }
}

// 动图设置GPU在线状态
async function getGpusystem_info() {
    try {
        const response = await fetch('/get_gpu_servers');
        const data = await response.json();

        // Check if the response has the expected structure
        if (data.hasOwnProperty('gpu_servers')) {
            const gpuServers = data.gpu_servers;
            // Loop through each GPU server and display information
            gpuServers.forEach(server => {
                // `ID: ${server.id}, Name: ${server.name}, Port: ${server.port}, Status: ${server.status}`;
                SetGPU_system_info(server.name,server.status);
            });
            
        } else {
            console.error('Unexpected response structure');
        }
    } catch (error) {
        console.error('Error fetching GPU server information:', error);
    }
}

function SetGPU_State(id,state) {
    // 获取指定 ID 下的类别为 exampleClass 的所有元素
    var containerDiv = document.getElementById(id);
    var elementsWithClass = containerDiv.getElementsByClassName('status');
    var elementsWithClass2 = containerDiv.getElementsByClassName('status1');

    // 获取第一个元素
    var statusElement = elementsWithClass[0];
    var statusElementText = elementsWithClass2[0];
    
    switch (state) {
        case 'idle':
            // 执行 idle 状态下的任务
            if (statusElementText) {
                // 修改文字
                statusElementText.innerHTML = 'idle';
                OnlineServerNum = OnlineServerNum + 1;

            }
            if (statusElement) {
                // 修改背景色
                statusElement.style.backgroundColor = '#99e948';
            }
            break;

        case 'busy':
            // 执行 busy 状态下的任务
            if (statusElementText) {
                // 修改文字
                statusElementText.innerHTML = 'busy';
                OnlineServerNum = OnlineServerNum + 1;
                Calculating = Calculating +1;
            }
            if (statusElement) {
                // 修改背景色
                statusElement.style.backgroundColor = '#eabe4c';
            }
            break;

        case 'offline':
            // 执行 offline 状态下的任务
            if (statusElementText) {
                // 修改文字
                statusElementText.innerHTML = 'offline';

            }
            if (statusElement) {
                // 修改背景色
                statusElement.style.backgroundColor = '#a0a0a0';
            }
            break;

    }

}

// 动态获取并设置GPU硬件信息
function SetGPU_system_info(id,state) {
    // 获取指定 ID 下的类别为 exampleClass 的所有元素
    var containerDiv = document.getElementById(id);
    if (state != 'offline') {
        switch (id) {
            case 'GPU1':
                get_system_info(containerDiv,5006)
                break;
    
            case 'GPU2':
                get_system_info(containerDiv,5007)
                break;
    
            case 'GPU3':
                get_system_info(containerDiv,5008)
                break;    
        }
    }    
}

// 获取GPU设备硬件信息
var elementswindows_version;
var elementsip;
var elementsmemory_info;
var elementsuptime;
var elementsnetwork_usage;
var elementsnetdisk_usage;
var elementsnetdownload_speed;
var elementsnetupload_speed;
var elementsnetcpu;
var elementsnetdisk;
var elementsnetram;
var elementsnetprogressCPU;
var elementsnetprogressDISK;
var elementsnetprogressRAM
async function get_system_info(containerDiv,port) {

    const timeoutPromise = new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 10000));

    try {
        const response = await Promise.race([fetch(ServerIP + ':' + port + '/get_system_info'), timeoutPromise]);
        const data = await response.json();
        
        // Check if the response has the expected structure
        if (data.hasOwnProperty('ip')) {
            platform = data.platform;
            version = data.version;
            ip = data.ip;
            memory_info = data.memory_info;
            uptime = data.uptime;
            network_usage = data.network_usage;
            disk_usage = data.disk_usage;
            download_speed = data.download_speed;
            upload_speed = data.upload_speed;
            cpu = data.cpu * 10;
            if (cpu > 100){
                cpu = 100;
            }
            disk = data.disk;
            memory = data.memory;

            // 设置硬件信息
            elementswindows_version = containerDiv.getElementsByClassName('Windows');
            elementswindows_version[0].innerHTML = platform +' '+ version;
            
            elementsip = containerDiv.getElementsByClassName('ip');
            elementsip[0].innerHTML = ip;

            elementsmemory_info = containerDiv.getElementsByClassName('memory_info');
            elementsmemory_info[0].innerHTML = memory_info;

            elementsuptime = containerDiv.getElementsByClassName('uptime');
            elementsuptime[0].innerHTML = uptime;

            elementsnetwork_usage = containerDiv.getElementsByClassName('network_usage');
            elementsnetwork_usage[0].innerHTML = network_usage;

            elementsnetdisk_usage = containerDiv.getElementsByClassName('disk_usage');
            elementsnetdisk_usage[0].innerHTML = disk_usage;

            elementsnetdownload_speed = containerDiv.getElementsByClassName('download_speed');
            elementsnetdownload_speed[0].innerHTML = download_speed.toFixed(2) + 'Kbps';

            elementsnetupload_speed = containerDiv.getElementsByClassName('upload_speed');
            elementsnetupload_speed[0].innerHTML = upload_speed.toFixed(2) + 'Kbps';

            elementsnetcpu = containerDiv.getElementsByClassName('cpu');
            elementsnetprogressCPU = containerDiv.getElementsByClassName('progressCPU');
            elementsnetcpu[0].innerHTML = cpu + "%";
            elementsnetprogressCPU[0].value = cpu;

            elementsnetdisk = containerDiv.getElementsByClassName('disk');
            elementsnetprogressDISK = containerDiv.getElementsByClassName('progressDISK');
            elementsnetdisk[0].innerHTML = disk + "%";
            elementsnetprogressDISK[0].value = disk;

            elementsnetram = containerDiv.getElementsByClassName('ram');
            elementsnetprogressRAM = containerDiv.getElementsByClassName('progressRAM');
            elementsnetram[0].innerHTML = memory + "%";
            elementsnetprogressRAM[0].value = memory;
        } 
    } catch (error) {
        console.error('Fetch error:', error);
    }
}

*************************************************************************************/