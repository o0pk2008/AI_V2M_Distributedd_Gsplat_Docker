// 全局变量

// 日志按钮
var button_log;

// socket接收
var socket;

// MainFrame
var MainFrame;

var stepnavIcon
var loadingIcon
var wrapper;

// StepNav
var stepnavIcon;
var lis;

// LOG面板
var outputLog_main;

// LOG面板隐藏状态
var hidden = true;

// 请求服务器日志-当前进度
var global_lastProgress = "calculate";

// CalculateBtn按钮
var CalculateBtn;

// 当页面渲染完毕后开始接收日志
document.addEventListener('DOMContentLoaded', function () {

    // 获取CalculateBtn元素
    CalculateBtn = document.querySelector('.CalculateBtn');

    // 检查CalculateBtn按钮是否存在
    if (CalculateBtn) {
        // 给按钮添加点击事件的监听器
        CalculateBtn.addEventListener('click', function () {
            SetStepBG(3);
        });
    }


    // socket接收
    socket = io.connect('http://' + document.domain + ':' + location.port);

    // 启动监听
    listener_log();

    // 初始化请求一次当前进度
    get_progress();

    // 持续请求当前进度
    setInterval(get_progress, 2000);

    // 获取OutputLog面板
    outputLog_main = document.querySelector('#outputLog_main');

    // 获取OutputLog面板按钮元素
    button_log = document.querySelector('.btn-outputlog');

    // 获取stepnavIcon元素 
    stepnavIcon = document.querySelector('.stepnav-icon');

    // 获取loading icon元素 
    loadingIcon = document.querySelector('.group-loading-icon');

    // 获取wrapper-image-bg元素 
    wrapper = document.querySelector('.wrapper-image-bg');

    // MainFrame
    MainFrame = document.querySelector('#MainFrame');

    // 默认加载首页
    loadPage_index();

    // StepNav
    stepnavIcon = document.querySelector('.stepnav-icon');
    lis = stepnavIcon.querySelectorAll('li');

    // 隐藏与显示OutputLog面板
    button_log.addEventListener('click', function () {
        // 切换按钮的翻转状态
        hidden = !hidden;

        // 根据翻转状态设置背景图像的翻转
        if (hidden) {
            button_log.style.transform = 'scaleY(-1)';
            outputLog_main.style.height = '40px';
            // 面板隐藏后执行
            loadingIcon.style.display = 'none';
            wrapper.style.filter = 'blur(0px)';
        } else {
            button_log.style.transform = 'scaleY(1)';
            outputLog_main.style.height = '300px';
            // 面板显示后执行
            checkAndExecute();
        }
    });

    // 运行计算管线
    // run_pipeline();

});

// 请求进度事件
function get_progress() {
    $.ajax({
        url: "/get_progress",
        type: "GET",
        dataType: "json",
        success: function (response) {
            if (response.progress !== null && response.progress !== global_lastProgress) {
                // 获取当前时间
                let currentTime = new Date().toLocaleString();
                console.log(currentTime + ":", response.progress);
                global_lastProgress = response.progress;
                // 执行对应进度事件
                handleProgressEvent();
            }
        },
        error: function (xhr, status, error) {
            console.error("Error:", error);
        }
    });
}


// 运行管线计算
async function run_pipeline() {
    let response = await fetch('/run_pipeline', {
        method: 'POST',
    });
}


// 接收日志
function listener_log() {
    socket.on('log', function (data) {
        // console.log(data);
        if (data.data != "") {
            // 获取当前时间
            let currentTime = new Date().toLocaleTimeString();
            let logElement = document.createElement('li');
            logElement.textContent = currentTime + " " + data.data;
            let logList = document.getElementById('loglist');
            // 获取当前列表中的第一个元素
            let firstLogElement = logList.firstChild;

            if (firstLogElement) {
                // 如果存在第一个元素，则插入到该元素之前
                logList.insertBefore(logElement, firstLogElement);
            } else {
                // 如果列表为空，则直接添加到列表末尾
                logList.appendChild(logElement);
            }
        }
    });
}

// 接收进度后的自动处理
function handleProgressEvent() {
    switch (global_lastProgress) {
        case "calculate":
            // 执行 calculate 对应的事件
            console.log("执行 calculate 对应的事件");
            // SetStepBG(3); //这里会重复执行
            break;
        case "sfm":
            // 执行 sfm 对应的事件
            console.log("执行 sfm 对应的事件");
            SetStepBG(4);
            break;
        case "dsm":
            // 执行 dsm 对应的事件
            console.log("执行 dsm 对应的事件");
            SetStepBG(5);
            break;
        case "dsm-fused":
            // 执行 dsm-fused 对应的事件
            console.log("执行 dsm-fused 对应的事件");
            SetStepBG(6);
            break;
        case "mesh":
            // 执行 mesh 对应的事件
            console.log("执行 mesh 对应的事件");
            SetStepBG(7);
            break;
        case "finish":
            // 执行 finish 对应的事件
            console.log("执行 finish 对应的事件");
            SetStepBG(8);
            break;
        default:
            // 如果 global_lastProgress 的值不在预期的列表中，可以在这里处理
            console.log("未知事件");
    }
}


// 设置STEP背景
function SetStepBG(num) {

    updateLiColor(num - 1);

    switch (num) {
        case 1:
            stepnavIcon.style.backgroundImage = "url('/static/public/StepNav_1.png')";
            loadingIcon.style.display = 'none';
            wrapper.style.filter = 'blur(0px)';
            loadPage_index();
            hiddenLog();
            showCalculateBtn(false);
            break;
        case 2:
            stepnavIcon.style.backgroundImage = "url('/static/public/StepNav_2.png')";
            loadingIcon.style.display = 'none';
            wrapper.style.filter = 'blur(0px)';
            loadPage_check_img();
            hiddenLog();
            showCalculateBtn(true);
            break;
        case 3:
            stepnavIcon.style.backgroundImage = "url('/static/public/StepNav_3.png')";
            showCalculateBtn(false);
            showLog();
            loadPage_Calculate();
            break;
        case 4:
            stepnavIcon.style.backgroundImage = "url('/static/public/StepNav_4.png')";
            showCalculateBtn(false);
            loadPage_sfmView();
            hiddenLog();
            break;
        case 5:
            stepnavIcon.style.backgroundImage = "url('/static/public/StepNav_5.png')";
            showCalculateBtn(false);
            break;
        case 6:
            stepnavIcon.style.backgroundImage = "url('/static/public/StepNav_6.png')";
            showCalculateBtn(false);
            loadPage_plyView();
            hiddenLog();
            break;
        case 7:
            stepnavIcon.style.backgroundImage = "url('/static/public/StepNav_7.png')";
            showCalculateBtn(false);
            loadPage_MeshView();
            hiddenLog();
            break;
        case 8:
            stepnavIcon.style.backgroundImage = "url('/static/public/StepNav_8.png')";
            loadingIcon.style.display = 'none';
            wrapper.style.filter = 'blur(0px)';
            showCalculateBtn(false);
            loadPage_objView();
            break;
        default:
            stepnavIcon.style.backgroundImage = "url('/static/public/StepNav_1.png')";
            loadingIcon.style.display = 'none';
            wrapper.style.filter = 'blur(0px)';
            showCalculateBtn(false);
            break;
    }
}

// 设置Step中li的文字颜色变化
function updateLiColor(startIndex) {
    for (var i = 0; i < lis.length; i++) {
        if (i <= startIndex) {
            lis[i].style.color = '#2AE5B3';
        } else {
            lis[i].style.color = 'white';
        }
    }
}

// LOG面板隐藏显示逻辑
function checkAndExecute() {
    switch (global_lastProgress) {
        case "calculate":
        case "sfm":
        case "dsm":
        case "dsm-fused":
        case "mesh":
            loadingIcon.style.display = "block";
            wrapper.style.filter = 'blur(10px)';
            break;
        default:
            // 如果 global_lastProgress 的值不在预期的列表中，可以在这里处理
            break;
    }
}

// MainFrame
function loadPage_index() {
    MainFrame.src = "/index";
    // 监听 iframe 的加载完成事件
    MainFrame.onload = function () {

        // 获取 iframe 页面中的按钮元素
        let index_button = MainFrame.contentWindow.document.querySelector('.btnstart');

        // 检查按钮是否存在
        if (index_button) {
            // 给按钮添加点击事件的监听器
            index_button.addEventListener('click', function () {
                SetStepBG(2);
            });
        }
    };
}

// 查看影像图片
function loadPage_check_img() {
    MainFrame.src = "/check_img";
}

// 计算时页面
function loadPage_Calculate() {
    MainFrame.src = "/Calculate";
    // 运行计算管线
    run_pipeline();
}

// 查看obj
function loadPage_objView() {
    MainFrame.src = "/objView";
}

// 查看mesh
function loadPage_MeshView() {
    MainFrame.src = "/MeshView";
}

// 查看sfmView
function loadPage_sfmView() {
    MainFrame.src = "/sfmView";
}

// 查看plyView
function loadPage_plyView() {
    MainFrame.src = "/plyView";
}

// LOG面板如果没有隐藏则隐藏
function hiddenLog() {
    hidden = true;
    button_log.style.transform = 'scaleY(-1)';
    outputLog_main.style.height = '40px';
    // 面板隐藏后执行
    loadingIcon.style.display = 'none';
    wrapper.style.filter = 'blur(0px)';
}

// LOG面板如果没有显示则显示
function showLog() {
    hidden = false;
    button_log.style.transform = 'scaleY(1)';
    outputLog_main.style.height = '300px';
    // 面板显示后执行
    checkAndExecute();
}

// 显示或隐藏开始计算按钮
function showCalculateBtn(show) {
    if (show) {
        CalculateBtn.style.display = "block"
    } else {
        CalculateBtn.style.display = "none"
    }
}