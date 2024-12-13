/*
  作者: Ning
  文件名: home.js
  描述: 这个文件包含了关于home.html页面的 JavaScript 代码。
  版本: 1.0.0
  最后修改日期: 2024-01-19
*/

// 获取具有 class 为 btn-updata 的元素
var button_upload = document.querySelectorAll('.btn-updata')[0];

// ClientServer_URL
var ClientServer_URL = "http://192.168.2.94:5000/";

// GPU_Manager_URL
var GPU_Manager_URL = "http://192.168.2.94:5200/";

// 模型下载页面
var iframeDocument;
var iframeWindow;
// 声明一个全局变量来存储 setTimeout 返回的标识符
let timerId;
let timerOBJ;

// 创建遮罩层元素
var overlay;

// 用户退出
function logout() {
    // 发起GET请求以清除会话
    fetch('/logout', {
        method: 'GET'
    }).then(response => {
        if (response.ok) {
            // 清除本地会话信息
            sessionStorage.clear();
            // 重定向到登录页面
            window.location.href = '/loginPage';
        } else {
            console.error('退出失败:', response.statusText);
            alert('退出失败，请稍后重试。');
        }
    }).catch(error => {
        console.error('发生错误:', error);
        alert('发生错误，请稍后重试。');
    });
}

// 储存服务地址
var updata_http;
var edit_http;

// 用于存储已执行代码的ID集合
var executedIDs = [];

// 判断轮询任务
var FinishIDs = [];

// 遍历所有匹配的元素并为其添加点击事件
if (button_upload) {
    button_upload.addEventListener('click', function () {
        // 显示上传组件
        showPopup("upload_drop")
    });
}

// 显示上传组件
function showPopup(name) {
    if (name == "upload_drop") {
        init_UploadDrop();
        // init_videoview();
        // init_uploadProgress();
    }
    var popup = document.getElementById('popup_main');
    popup.style.display = 'block';
}

// 隐藏上传组件
function hidePopup() {
    var popup = document.getElementById('popup_main');
    popup.style.display = 'none';
    // 移除遮罩层
    overlay.remove();
}

// 显示上传页面 并检测视频规则
function init_UploadDrop() {

    // 创建遮罩层元素
    overlay = document.createElement('div');
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100%';
    overlay.style.height = '100%';
    overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.5)'; // 半透明灰色背景
    overlay.style.backdropFilter = 'blur(5px)'; // 背景模糊效果
    overlay.style.zIndex = '1'; // 确保遮罩层在最上层显示
    // 将遮罩层添加到页面中
    document.body.appendChild(overlay);

    // 获取 iframe 元素
    var iframe = document.getElementById('createFrame');

    // 设置 iframe 的 src 属性为指定的 URL
    // iframe.src = "./FrameCreate.html";
    iframe.src = "./iframe_upload.html";

    // 等待 iframe 加载完成后执行操作
    iframe.onload = function () {
        // 从 iframe 中获取 class 为 button 的元素
        var buttonInIframe = iframe.contentDocument.getElementsByClassName('x-close2')[0];
        var dropInIframe = iframe.contentDocument.getElementsByClassName('drop')[0];

        // 隐藏该组件
        buttonInIframe.addEventListener('click', function () {
            hidePopup();
        });
        // 上传事件
        dropInIframe.addEventListener('click', function () {
            // 触发文件上传对话框
            var input = document.createElement('input');
            input.type = 'file';
            input.accept = '.mp4, .mov';
            input.click();
            input.addEventListener('change', function () {
                // 处理选定的文件
                var selectedFile = input.files[0];

                // 检查文件是否存在
                if (!selectedFile) {
                    alert('请选择一个视频文件');
                    return;
                }

                // 使用HTMLMediaElement来获取视频时长
                var video = document.createElement('video');
                var objectURL = URL.createObjectURL(selectedFile);
                video.src = objectURL;
                // console.log(objectURL);

                video.onloadedmetadata = function () {
                    // 获取视频时长（以秒为单位）
                    var duration = video.duration;

                    // 判断和限制视频时长
                    var minDuration = 10;
                    var maxDuration = 180;
                    if (duration > maxDuration) {
                        alert('请选择一个时长小于3分钟的文件');
                        return;
                    } else if (duration < minDuration) {
                        alert('请选择一个时长大于10秒的文件');
                        return;
                    }

                    // 检查文件大小（以字节为单位）
                    var fileSize = selectedFile.size;
                    // 判断和限制视频体积
                    var maxSize = 1 * 1024 * 1024 * 1024;
                    if (fileSize > maxSize) {
                        alert('请选择一个小于1GB的文件');
                        // 清空文件选择，防止用户选择过大的文件后提交
                        input.value = '';
                        return;
                    }
                };

                // 切换上传页面
                hidePopup();

                // 显示页面预览视频
                init_videoview(selectedFile);

            });
        });
    };
}
// 显示视频预览页面
function init_videoview(selectedFile) {
    // 获取 iframe 元素
    var iframe = document.getElementById('createFrame');

    // 创建遮罩层元素
    overlay = document.createElement('div');
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100%';
    overlay.style.height = '100%';
    overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.5)'; // 半透明灰色背景
    overlay.style.backdropFilter = 'blur(5px)'; // 背景模糊效果
    overlay.style.zIndex = '1'; // 确保遮罩层在最上层显示
    // 将遮罩层添加到页面中
    document.body.appendChild(overlay);

    // 设置 iframe 的 src 属性为指定的 URL
    // iframe.src = "./FrameCreator.html";
    iframe.src = "./project_information.html";

    // 等待 iframe 加载完成后执行操作
    iframe.onload = function () {
        // 从 iframe 中获取 class 为 button 的元素
        var buttonInIframe = iframe.contentDocument.getElementsByClassName('x-close1')[0];
        var videoIframe = iframe.contentDocument.getElementsByClassName('frame-video')[0];
        var buttonupdata = iframe.contentDocument.getElementsByClassName('buttonupdata')[0];
        var input_title = iframe.contentDocument.getElementsByClassName('input_title')[0];
        var input_privacy = iframe.contentDocument.getElementsByClassName('userprivacy')[0];
        var input_export_mesh = iframe.contentDocument.getElementsByClassName('export_mesh')[0];

        // 隐藏该组件
        buttonInIframe.addEventListener('click', function () {
            hidePopup();
        });

        const videoURL = URL.createObjectURL(selectedFile);

        // 设置视频
        videoIframe.src = videoURL;

        // 重新加载视频
        videoIframe.load();

        // 显示当前组件
        var popup = document.getElementById('popup_main');
        popup.style.display = 'block';

        // 点击进行视频处理
        buttonupdata.addEventListener('click', function () {
            // 获取是否进行mesh导出勾选值
            let CheckedintValue = input_export_mesh.checked ? 1 : 0;
            hidePopup();
            updata_video(selectedFile, input_title.value, input_privacy.value, CheckedintValue);
        });
    }
}

// Helper函数：创建带有上传进度事件的XMLHttpRequest
function createXmlHttpRequest() {
    const xhr = new XMLHttpRequest();
    return xhr;
}

// 执行上传并显示上传进度
function init_uploadProgress(selectedFile, project_name, input_privacy, export_mesh) {
    // 获取 iframe 元素
    var iframe = document.getElementById('createFrame');

    // 设置 iframe 的 src 属性为指定的 URL
    // iframe.src = "./FrameRoot.html";
    iframe.src = "./iframe_progressBar.html";

    // 等待 iframe 加载完成后执行操作
    iframe.onload = function () {
        // 从 iframe 中获取 class 为 button 的元素
        // var buttonInIframe = iframe.contentDocument.getElementsByClassName('x-close')[0];
        // 获取进度条组件
        const progressBar = iframe.contentDocument.getElementById('progressBar');
        // 获取进度文字
        var progresstextInIframe = iframe.contentDocument.getElementsByClassName('div4')[0];

        const xhr = createXmlHttpRequest();

        xhr.open('POST', '/upload', true);

        // 上传进度事件处理程序
        xhr.upload.addEventListener('progress', (event) => {
            if (event.lengthComputable) {
                const percentComplete = (event.loaded / event.total) * 100;
                // progressBar.value = percentComplete;
                progresstextInIframe.innerHTML = Math.round(percentComplete) + " %";
                progressBar.style.width = `${Math.round(percentComplete) + "%"}`;
            }
        });

        // 文件上传完成后的处理
        xhr.onreadystatechange = function () {
            if (xhr.readyState === XMLHttpRequest.DONE) {
                if (xhr.status === 200) {
                    // console.log('File uploaded successfully!');
                    // 显示状态
                    progresstextInIframe.innerHTML = "数据上传成功，正在处理...";

                    // 解析message字段中的JSON字符串
                    var messageObject = JSON.parse(xhr.responseText);
                    // console.log("messageObject.folder_path", messageObject.folder_path);
                    // console.log("messageObject.file_path", messageObject.file_path);
                    // console.log("messageObject.folder_name", messageObject.folder_name);
                    // console.log("messageObject.status", messageObject.status);

                    if (messageObject.status) {
                        // 显示状态
                        progresstextInIframe.innerHTML = "数据上传成功";

                        // 执行姿态计算
                        // run_convert(messageObject.folder_path, messageObject.file_path, messageObject.folder_name);

                        // 隐藏上传进度控件
                        hidePopup();

                        // 进行全局数据刷新
                        get_data_from_serve();
                    } else {
                        progresstextInIframe.innerHTML = "数据处理失败，请检查文件";
                    }
                } else {
                    console.log('File upload failed!');
                }
            }
        };

        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('name', project_name);
        formData.append('input_privacy', input_privacy);
        formData.append('user_name', UserName);
        formData.append('user_id', UserID);
        formData.append('export_mesh', export_mesh);

        // 发送文件数据
        xhr.send(formData);

        // 隐藏该组件
        // buttonInIframe.addEventListener('click', function () {
        //     hidePopup();
        // });
    }
}

// 视频上传事件
function updata_video(selectedFile, project_name, input_privacy, export_mesh) {
    // 执行上传逻辑
    if (selectedFile) {

        // 显示当前组件
        var popup = document.getElementById('popup_main');
        popup.style.display = 'block';

        init_uploadProgress(selectedFile, project_name, input_privacy, export_mesh);

    } else {
        console.error('No file selected');
    }
}

// 处理项目列表数据
function handleProjectList(data, search) {
    // 解析 JSON 数据
    // 解析message字段中的JSON字符串
    var messageObject = JSON.parse(data.message);
    var projects = messageObject.projects;
    var otherProjects = messageObject.otherProjects;
    updata_http = messageObject.updata_http;
    edit_http = messageObject.edit_http;

    // 获取主机IP
    var currentLocation = window.location;
    var serveIP = ClientServer_URL;

    // 判断如果存在项目则切换显示项目列表页面
    if (projects.length) {
        // toggleDisplay('list');
    }

    // 获取项目容器
    var projectsContainer = document.getElementsByClassName('My_Captures')[0];
    var shareContainer = document.getElementsByClassName('Explore')[0];

    // 清空现有的MyCaptures列表 执行一次
    let hasBeenExecuted_My_Captures = false;
    function Clear_My_Captures_Once() {
        if (!hasBeenExecuted_My_Captures) {
            // 在第一次执行时 清空现有的MyCaptures列表
            if (projectsContainer) {
                projectsContainer.innerHTML = '';
            }
            // 设置标志为 true，表示已经执行过
            hasBeenExecuted_My_Captures = true;
        }
    }

    // 使用 reverse 方法将数组反转
    projects.reverse();

    // 动态创建产品列表
    projects.forEach(function (projectSql, index) {
        // 判断是否存在用户自定义名称
        var project_name = projectSql[4];
        var id_data_pointer = 4;
        if (project_name == "default") {
            id_data_pointer = 1;
        }
        // 使用模板字符串创建HTML字符串
        var MyCapturesHtml = `
                    <div class="relative thumbnail ${projectSql[1]}" data-status="idle">
                        <a href="#" target="_blank" class="thumbnail-link viewLink">
                            <img src="./img/300x200.png" alt="${projectSql[1]}"
                                class="w-full h-56 object-cover bg-gray-200 rounded-md overflow-hidden rounded-md overflow-hidden ListImg">
                        </a>
                        <div class="px-0 py-2">
                            <h3 class="text-gray-800 font-medium truncate">${projectSql[id_data_pointer]}</h3>
                        </div>
                        <div class="absolute top-5 right-5 flex space-x-2 opacity-0 thumbnail-buttons transition duration-300">
                            <button class="bg-opacity-80 bg-gray-200 text-gray-600 p-2 rounded-full hover:bg-gray-100">
                                <i data-feather="share-2" class="w-4 h-4"></i>
                            </button>
                            <button class="bg-opacity-80 bg-gray-200 text-gray-600 p-2 rounded-full hover:bg-gray-100 Btn_down">
                                <i data-feather="download" class="w-4 h-4"></i>
                            </button>
                            <button class="bg-opacity-80 bg-gray-200 text-gray-600 p-2 rounded-full hover:bg-gray-100 Btn_editor">
                                <i data-feather="edit" class="w-4 h-4"></i>
                            </button>
                            <button class="bg-opacity-80 bg-gray-200 text-gray-600 p-2 rounded-full hover:bg-gray-100 Btn_delete">
                                <i data-feather="trash" class="w-4 h-4"></i>
                            </button>
                        </div>
                        <div class="absolute bottom-4 left-0 w-full h-full flex items-center justify-center thumbnail-loading">
                            <div class="progress-indicator">
                                <div class="progress-circle"></div>
                                <span class="ml-2 text-white progressText">Calculating...</span>
                            </div>
                        </div>
                    </div>
                `;

        // 判断是我的模型还是共享模型-改为服务器判断
        // 清空现有的MyCaptures列表 执行一次
        Clear_My_Captures_Once();

        // 插入HTML字符串到容器中
        if (projectsContainer) {
            projectsContainer.insertAdjacentHTML('afterbegin', MyCapturesHtml);
        }

        // 打印用户ID
        // console.log(projectSql[3]);

        // 更新数据
        if (projectsContainer) {

            // 获取项目元素
            var Elements_project = document.getElementsByClassName(projectSql[1])[0];
            // 获取图片超链接元素
            var Elements_viewLink = Elements_project.getElementsByClassName('viewLink')[0];
            // 获取下载按钮元素
            var Elements_Btn_down = Elements_project.getElementsByClassName('Btn_down')[0];
            // 获取编辑按钮元素
            var Elements_Btn_editor = Elements_project.getElementsByClassName('Btn_editor')[0];
            // 获取删除按钮元素
            var Elements_Btn_delete = Elements_project.getElementsByClassName('Btn_delete')[0];

            // 增加删除数据事件
            if (Elements_Btn_delete) {
                Elements_Btn_delete.addEventListener('click', function () {
                    // 传递ID给删除函数
                    deleteDataFromID(projectSql[1]);
                });
            }

            // 判断项目状态 训练-0 or 完成-1
            if (projectSql[6]) {
                if (Elements_project) {

                    // 设置新的 data-status 值
                    Elements_project.setAttribute('data-status', 'idle');

                    // 获取图片元素
                    var childElements_Proj = Elements_project.getElementsByClassName('ListImg')[0];

                    // 检查对象是否被编辑
                    if (projectSql[8]) {

                        // 设置查看超链接在新窗口
                        let editFilePath = encodeURIComponent(updata_http + "uploads/" + projectSql[1] + "/edit/Editfile.ply");
                        let projectName = projectSql[id_data_pointer];
                        let author = encodeURIComponent(projectSql[3]);
                        // let viewerUrl = "./viewer.html?url=" + encodeURIComponent(edit_http + "/edit/?plyFilePath=" + editFilePath + "&color=" + projectSql[12] + "&idkey=" + projectSql[0] + "&serveIP=" + serveIP) + "&name=" + projectName + "&author=" + author;
                        let viewerUrl = "./viewer.html?url=" + encodeURIComponent(edit_http + "/edit/?idkey=" + projectSql[0] + "&serveIP=" + serveIP) + "&name=" + projectName + "&author=" + author;
                        Elements_viewLink.href = viewerUrl;

                        // 添加下载事件监听
                        // AddDownLoadListener(Elements_Btn_down, updata_http + "uploads/" + projectSql[1] + "/edit/Editfile.ply", projectSql[1] + ".ply");
                        AddN2MListener(Elements_Btn_down, projectSql[1])

                        // 设置编辑超链接 &serveIP 用于保存时与flask通信
                        // Elements_Btn_editor.href = "" + edit_http + "/edit/?plyFilePath=" + updata_http + "uploads/" + projectSql[1] + "/edit/Editfile.ply&id=" + projectSql[1] + "&edit=true" + "&serveIP=" + serveIP;

                        // let viewerUrlEcitor = "./editor.html?url=" + encodeURIComponent(edit_http + "/edit/?plyFilePath=" + editFilePath + "&id=" + projectSql[1] + "&edit=true" + "&serveIP=" + serveIP + "&color=" + projectSql[12]);
                        let viewerUrlEcitor = "./editor.html?url=" + encodeURIComponent(edit_http + "/edit/?id=" + projectSql[1] + "&edit=true" + "&serveIP=" + serveIP + "&idkey=" + projectSql[0]);

                        // 添加点击事件监听器
                        Elements_Btn_editor.addEventListener('click', function () {
                            // 在新窗口打开链接
                            window.open(viewerUrlEcitor, '_blank');
                        });
                    }
                    else {
                        // 设置查看超链接
                        // Elements_viewLink.href = "" + edit_http + "/edit/?plyFilePath=" + updata_http + "uploads/" + projectSql[1] + "/splat.ply";
                        // 设置查看超链接在新窗口
                        let editFilePath = encodeURIComponent(updata_http + "uploads/" + projectSql[1] + "/splat.ply");
                        let projectName = projectSql[id_data_pointer];
                        let author = encodeURIComponent(projectSql[3]);
                        // let viewerUrl = "./viewer.html?url=" + encodeURIComponent(edit_http + "/edit/?plyFilePath=" + editFilePath + "&color=" + projectSql[12] + "&idkey=" + projectSql[0] + "&serveIP=" + serveIP) + "&name=" + projectName + "&author=" + author;
                        let viewerUrl = "./viewer.html?url=" + encodeURIComponent(edit_http + "/edit/?idkey=" + projectSql[0] + "&serveIP=" + serveIP) + "&name=" + projectName + "&author=" + author;
                        Elements_viewLink.href = viewerUrl;


                        // 添加下载事件监听
                        // AddDownLoadListener(Elements_Btn_down, updata_http + "uploads/" + projectSql[1] + "/splat.ply", projectSql[1] + ".ply");
                        AddN2MListener(Elements_Btn_down, projectSql[1])

                        // 设置编辑超链接 &serveIP 用于保存时与flask通信
                        // Elements_Btn_editor.href = "" + edit_http + "/edit/?plyFilePath=" + updata_http + "uploads/" + projectSql[1] + "/splat.ply&id=" + projectSql[1] + "&edit=true" + "&serveIP=" + serveIP;
                        // let viewerUrlEcitor = "./editor.html?url=" + encodeURIComponent(edit_http + "/edit/?plyFilePath=" + editFilePath  + "&id=" + projectSql[1] + "&edit=true" + "&serveIP=" + serveIP + "&color=" + projectSql[12]);
                        let viewerUrlEcitor = "./editor.html?url=" + encodeURIComponent(edit_http + "/edit/?id=" + projectSql[1] + "&edit=true" + "&serveIP=" + serveIP + "&idkey=" + projectSql[0]);
                        // 添加点击事件监听器
                        Elements_Btn_editor.addEventListener('click', function () {
                            // 在新窗口打开链接
                            window.open(viewerUrlEcitor, '_blank');
                        });
                    }

                    if (childElements_Proj) {
                        // 设置新的图像源路径
                        childElements_Proj.setAttribute('src', updata_http + "uploads/" + projectSql[1] + "/sfm/images_4/frame_00001.png");
                    }
                    else {
                        console.error("没有找到具有 'childElements_Proj' 类的元素");
                    }
                }
                else {
                    console.error("没有找到具有 'Elements_project' 类的元素");
                }
            }
            // 未计算完成的显示计算进度
            else {
                if (Elements_project) {

                    // 设置新的 data-status 值
                    Elements_project.setAttribute('data-status', 'loading');

                    // 获取图片元素
                    var childElements_Proj = Elements_project.getElementsByClassName('ListImg')[0];

                    // 获取进度文本元素
                    let childElements_progressText = Elements_project.getElementsByClassName('progressText')[0];

                    // 设置编辑按钮链接
                    Elements_Btn_editor.href = "#";

                    // 设置图片超链接
                    Elements_viewLink.href = "#";

                    // 设置进度文本
                    childElements_progressText.innerHTML = projectSql[7];

                    if (childElements_Proj) {
                        // 如果还未进行视频转换则显示等待图像
                        if (projectSql[7] == "Queue") {
                            // 设置新的图像源路径
                            childElements_Proj.setAttribute('src', '/public/Wait_BG.png');
                        }
                        // 服务器已经转换了视频则显示视频缩略图
                        else {
                            // 设置新的图像源路径
                            childElements_Proj.setAttribute('src', updata_http + "uploads/" + projectSql[1] + "/sfm/images_4/frame_00001.png");
                            // 设置图片高斯
                            childElements_Proj.style.filter = "blur(3px)";
                        }

                    }
                    else {
                        console.error("没有找到具有 'childElements_Proj' 类的元素");
                    }

                    // 请求进度信息<!仅测试版本使用>
                    startEvent(projectSql[1], childElements_progressText, projectSql[1]);
                }
                else {
                    console.error("没有找到具有 'Elements_project' 类的元素");
                }
            }
        }


    })

    // 如果不是搜索则正常渲染
    if (!search) {
        // 清空现有的Explore列表 执行一次
        let hasBeenExecuted_Explore = false;
        function Clear_Explore_Once() {
            if (!hasBeenExecuted_Explore) {
                // 在第一次执行时 清空现有的Explore列表
                // 清空现有的EXPORE列表
                if (shareContainer) {
                    shareContainer.innerHTML = '';
                }
                // 设置标志为 true，表示已经执行过
                hasBeenExecuted_Explore = true;
            }
        }

        // 在这里执行清除Explore
        Clear_Explore_Once();

        // 动态创建产品列表
        otherProjects.forEach(function (projectSql, index) {
            // 判断是否存在用户自定义名称
            var project_name = projectSql[4];
            var id_data_pointer = 4;
            if (project_name == "default") {
                id_data_pointer = 1;
            }

            // 共享模型
            // 判断是否公开
            if (projectSql[5]) {
                // 判断共享模型是否训练完成 仅显示已完成的
                if (projectSql[6]) {
                    // 使用模板字符串创建HTML字符串
                    var ExploreHtml = `
                        <div class="relative ${projectSql[1]}" data-status="idle">
                            <a href="#" target="_blank" class="thumbnail-link viewLink">
                                <img src="./img/300x200.png" alt="${projectSql[1]}"
                                    class="w-full h-56 object-cover rounded-md overflow-hidden ListImg">
                            </a>
                            <div class="absolute bottom-12 left-2 p-2 bg-black bg-opacity-40 rounded-lg text-white text-xs AuthorID">
                                @Ning+
                            </div>
                            <div class="px-0 py-2">
                                <h3 class="text-gray-800 font-medium truncate">${projectSql[id_data_pointer]}</h3>
                            </div>
                        </div>
                    `;
                    // 插入HTML字符串到容器中
                    if (shareContainer) {
                        shareContainer.insertAdjacentHTML('beforeend', ExploreHtml);
                    }

                    // 更新数据
                    if (shareContainer) {
                        // 获取当前页面元素数量
                        // var projectsContainerChildLength = shareContainer.getElementsByClassName('project').length;
                        // 获取项目元素
                        // var Elements_project = shareContainer.getElementsByClassName('project')[projectsContainerChildLength - 1];
                        var Elements_project = document.getElementsByClassName(projectSql[1])[0];
                        // 获取图片超链接元素
                        var Elements_viewLink = Elements_project.getElementsByClassName('viewLink')[0];
                        // 获取作者控件
                        var childElements_author = Elements_project.getElementsByClassName('AuthorID')[0];
                        // 显示共享模型的作者信息
                        childElements_author.style.display = 'flex';
                        childElements_author.innerHTML = '@' + projectSql[3];

                        if (Elements_project) {

                            // 获取图片元素
                            var childElements_Proj = Elements_project.getElementsByClassName('ListImg')[0];

                            // 检查对象是否被编辑
                            if (projectSql[8]) {
                                // 设置查看超链接
                                let projectName = projectSql[id_data_pointer];
                                let author = encodeURIComponent(projectSql[3]);
                                let viewerUrl = "./viewer.html?url=" + encodeURIComponent(edit_http + "/edit/?idkey=" + projectSql[0] + "&serveIP=" + serveIP) + "&name=" + projectName + "&author=" + author;
                                Elements_viewLink.href = viewerUrl;
                            }
                            else {
                                // 设置查看超链接
                                let projectName = projectSql[id_data_pointer];
                                let author = encodeURIComponent(projectSql[3]);
                                let viewerUrl = "./viewer.html?url=" + encodeURIComponent(edit_http + "/edit/?idkey=" + projectSql[0] + "&serveIP=" + serveIP) + "&name=" + projectName + "&author=" + author;
                                Elements_viewLink.href = viewerUrl;
                            }

                            if (childElements_Proj) {
                                // 设置新的图像源路径
                                childElements_Proj.setAttribute('src', updata_http + "uploads/" + projectSql[1] + "/sfm/images_4/frame_00001.png");
                            }
                            else {
                                console.error("没有找到具有 'childElements_Proj' 类的元素");
                            }
                        }
                        else {
                            console.error("没有找到具有 'Elements_project' 类的元素");
                        }

                    }
                }
            }

        })

    }

};

// 从服务器请求数据
function get_data_from_serve() {

    // 从 URL 中获取 page 参数
    var urlParams = new URLSearchParams(window.location.search);
    var page = urlParams.get('page') || 1; // 如果 URL 中没有提供 page 参数，默认为 1

    // 构造请求对象
    var requestOptions = {
        method: 'POST',  // 或者 'GET'，取决于你的后端路由
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ page: page, search: '' })
    };

    // 发送fetch请求
    fetch('/get_data', requestOptions)
        .then(response => response.json())
        .then(data => {
            // 检查服务器响应中的 status 字段
            if (data.status === 'success') {
                // 处理收到的服务器数据
                // 局部刷新Captures List数据
                handleProjectList(data, false);

                // 添加动画触发类以播放动画
                document.getElementById('MyCapturesContainer').classList.add('animate');

                // 添加动画触发类以播放动画
                document.getElementById('exploreContainer').classList.add('animate');

                // 刷新列表显示状态
                reashListState();
                // 动态生成分页导航
                let get_dataObject = JSON.parse(data.message);
                generatePagination(get_dataObject.totalPages, page);
            } else {
                console.error('服务器返回错误:', data.error);
            }
        })
        .catch(error => {
            console.error('发生错误:', error);
        });
}

// 动态生成分页
function generatePagination(totalPages, currentPage) {
    const paginationContainer = document.getElementById('pagination');
    if (paginationContainer) {
        paginationContainer.innerHTML = '';

        // Previous button
        const prevPage = Math.max(currentPage - 1, 1);
        paginationContainer.innerHTML += `
            <a href="?page=${prevPage}" class="relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0">
                <span class="sr-only">Previous</span>
                <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                    <path fill-rule="evenodd" d="M12.79 5.23a.75.75 0 01-.02 1.06L8.832 10l3.938 3.71a.75.75 0 11-1.04 1.08l-4.5-4.25a.75.75 0 010-1.08l4.5-4.25a.75.75 0 011.06.02z" clip-rule="evenodd" />
                </svg>
            </a>
        `;

        // Page numbers
        for (let page = 1; page <= totalPages; page++) {
            paginationContainer.innerHTML += `
                <a href="?page=${page}" class="relative inline-flex items-center px-4 py-2 text-sm font-semibold ${page == currentPage ? 'bg-indigo-600 text-white' : 'text-gray-900 ring-1 ring-inset ring-gray-300 hover:bg-gray-50'} focus:z-20 focus:outline-offset-0">
                    ${page}
                </a>
            `;
        }

        // Next button
        const nextPage = Math.min(currentPage + 1, totalPages);
        paginationContainer.innerHTML += `
            <a href="?page=${nextPage}" class="relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0">
                <span class="sr-only">Next</span>
                <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                    <path fill-rule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clip-rule="evenodd" />
                </svg>
            </a>
        `;
    }

}

// 移除动画触发类以重新播放动画
function replayAnimation() {
    var MyCapturesContainer = document.getElementById('MyCapturesContainer');

    // 获取MyCapturesContainer元素的样式对象
    var MyCapturesContainerStyle = document.getElementById('MyCapturesContainer').style;

    // 修改transition属性中的时间值为1秒
    MyCapturesContainerStyle.transition = 'opacity 0s ease-in-out';

    // 移除动画触发类以重新播放动画
    MyCapturesContainer.classList.remove('animate');

    // 延迟一点时间再次添加动画触发类以播放动画
    setTimeout(function () {
        // 修改transition属性中的时间值为1秒
    MyCapturesContainerStyle.transition = 'opacity 0.5s ease-in-out';
        MyCapturesContainer.classList.add('animate');
    }, 20); // 10毫秒的延迟，你可以根据需要调整这个值
}


// 列表搜索-不刷新页面
function searchList(search) {
    // 从 URL 中获取 page 参数
    var urlParams = new URLSearchParams(window.location.search);
    var page = urlParams.get('page') || 1; // 如果 URL 中没有提供 page 参数，默认为 1

    // 获取按钮元素
    const cancelBtn = document.getElementById('CancelBtn');
    cancelBtn.classList.remove('hidden');

    // 获取输入框元素
    const searchInput = document.getElementById('searchInput');

    // 监听Cancel按钮点击事件
    cancelBtn.addEventListener('click', function () {
        searchList("");
        searchInput.value = ''; // 清空输入框的值
        cancelBtn.classList.add('hidden');
    });

    // 构造请求对象
    var requestOptions = {
        method: 'POST',  // 或者 'GET'，取决于你的后端路由
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ page: page, search: search })
    };

    // 发送fetch请求
    fetch('/get_data', requestOptions)
        .then(response => response.json())
        .then(data => {
            // 检查服务器响应中的 status 字段
            if (data.status === 'success') {
                let get_dataObject = JSON.parse(data.message);
                if (get_dataObject.projects.length != 0) {
                    // 处理收到的服务器数据
                    // 全局刷新数据
                    handleProjectList(data, true);

                    // 重新播放动画函数
                    replayAnimation();

                    // 刷新列表显示状态
                    reashListState();
                    // 动态生成分页导航                
                    generatePagination(get_dataObject.totalPages, page);
                }
                else {
                    notification();
                }
            } else {
                console.error('服务器返回错误:', data.error);
            }
        })
        .catch(error => {
            console.error('发生错误:', error);
        });
}


// 如果有计算中的项目则每1秒请求一次进度<!仅测试版本使用>
// 创建一个对象来存储定时器
var timers = {};

// 设置每n秒执行一次的事件
function startEvent(timerId, ProgressElement, ID) {
    timers[timerId] = setInterval(function () {
        // progressByID(ProgressElement, ID);
        // 从GPU获取进度
        // Get_GPU_ProgressByID(ProgressElement, ID);
        // 从本地数据库获取进度
        Get_SQLData_ProgressByID(ProgressElement, ID);
    }, 5000);
}

// 取消定时事件
function stopEvent(timerId) {
    clearInterval(timers[timerId]);
    get_data_from_serve();
    // 刷新当前页面
    // location.reload();
    // 关闭轮询暂时有BUG

    // console.log('计算已完成');
}


// 从ID删除数据
function deleteDataFromID(ID) {
    // 弹出确认提示框
    var confirmDelete = confirm("确认删除？");

    // 如果用户点击了确认按钮
    if (confirmDelete) {
        // 构造请求对象
        var requestOptions = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ id: ID })
        };

        // 发送fetch请求
        fetch('/delete', requestOptions)
            .then(response => response.json())
            .then(data => {
                // console.log('成功收到响应:', data);
                // 在这里处理后端的响应
                // 进行全局数据刷新
                get_data_from_serve();
            })
            .catch(error => {
                console.error('发生错误:', error);
            });
    } else {
        // 用户点击了取消按钮，不执行删除操作
        console.log('删除操作已取消');
    }
}


// 从ID进行点赞
function AddLikeFromID(ID, childElements) {
    // 添加页面计数
    childElements.innerHTML = parseInt(childElements.innerHTML, 10) + 1;
    // 构造请求对象
    var requestOptions = {
        method: 'POST',  // 或者 'GET'，取决于你的后端路由
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ id: ID })
    };

    // 发送fetch请求
    fetch('/AddLike', requestOptions)
        .then(response => response.json())
        .then(data => {
            // console.log('成功收到响应:', data);
            // 在这里处理后端的响应
        })
        .catch(error => {
            console.error('发生错误:', error);
        });
}

// 执行下载.ply事件监听
function AddDownLoadListener(Element, href, name) {
    Element.addEventListener('click', function () {
        // 设置按钮的链接和下载属性
        this.href = href;
        this.download = name;
    });
}

// 加载下载页面 修改日期20240426
function AddN2MListener(Element, ID) {
    Element.addEventListener('click', function () {
        // 弹窗下载页面
        // loadPageInOverlay('./DownloadPage.html', ID)

        // 加载裁剪与下载页面
        let viewerUrl = "./CropTools.html?url=" + encodeURIComponent(edit_http + "/CropTools/?idkey=" + ID + "&updata_http=" + updata_http + "&serveIP=" + ClientServer_URL);

        // 在新窗口中打开指定的 URL
        window.open(viewerUrl, '_blank');
    });
}

// 加载页面到iframe
function loadPageInOverlay(url, ID) {
    // 创建遮罩层元素
    const overlay = document.createElement('div');
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100%';
    overlay.style.height = '100%';
    overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.5)'; // 半透明灰色背景
    overlay.style.backdropFilter = 'blur(5px)'; // 背景模糊效果
    overlay.style.zIndex = '9990'; // 确保遮罩层在最上层显示

    // 创建iframe元素
    const iframe = document.createElement('iframe');
    iframe.src = url;
    iframe.style.display = 'block';
    iframe.style.width = '650px';
    iframe.style.height = '680px';
    // iframe.style.backgroundColor = 'white';
    iframe.style.border = 'none';
    iframe.style.margin = 'auto';
    iframe.style.position = 'absolute';
    iframe.style.top = '50%';
    iframe.style.left = '50%';
    iframe.style.transform = 'translate(-50%, -50%)'; // 居中显示

    // 将iframe添加到遮罩层中
    overlay.appendChild(iframe);

    // 将遮罩层添加到页面中
    document.body.appendChild(overlay);

    // 等待iframe加载完毕
    iframe.onload = function () {

        iframeDocument = iframe.contentWindow.document;
        iframeWindow = iframe.contentWindow;

        const Button_crop = iframeDocument.getElementById('cropBtn');
        const exportcloseBtn = iframeDocument.getElementById('close-button');

        const Button_exportply = iframeDocument.getElementById('Export_ply');

        // 执行Nerf进度查询 并查询obj转换进度和状态
        Get_SQLData_NeRF_ProgressByID(ID);

        // 确保exportcloseBtn存在
        if (exportcloseBtn) {
            // 绑定exportcloseBtn点击事件
            exportcloseBtn.addEventListener('click', function () {
                // 停止执行 setTimeout 中的函数
                clearTimeout(timerId);
                clearTimeout(timerOBJ);
                // 清理iframe内部资源
                iframe.src = 'about:blank';
                // 移除遮罩层
                overlay.remove();
            });
        } else {
            console.error('Could not find the "close-button" button in the iframe.');
        }

        // 自定义裁剪工具
        if (Button_crop) {
            // 绑定Button_crop点击事件
            Button_crop.addEventListener('click', function () {
                // 加载调整页面
                let viewerUrl = "./CropTools.html?url=" + encodeURIComponent(edit_http + "/CropTools/?idkey=" + ID + "&updata_http=" + updata_http + "&serveIP=" + ClientServer_URL);

                // 在新窗口中打开指定的 URL
                window.open(viewerUrl, '_blank');
                // console.log(ID);
                // 弹出窗口
                // loadPageCropTools(viewerUrl)

                // 停止执行 setTimeout 中的函数
                // clearTimeout(timerId);
                // clearTimeout(timerOBJ);
                // 清理iframe内部资源
                // iframe.src = 'about:blank';
                // 移除遮罩层
                // overlay.remove();

            });
        } else {
            console.error('Could not find the "close-button" button in the iframe.');
        }

        // 下载PLY模型事件
        if (Button_exportply) {
            Button_exportply.addEventListener('click', () => {
                console.log("ExportPly");
                // 设置按钮的链接和下载属性
                let fileUrl = updata_http + "uploads/" + ID + "/pcd/point_cloud.ply";
                let a = document.createElement('a');
                a.href = fileUrl;
                a.download = 'file.pdf'; // 设置下载的文件名
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
            });
        }
    };

}

// 加载页面到iframe2
function loadPageCropTools(url2) {

    // 创建遮罩层元素
    const overlay2 = document.createElement('div');
    overlay2.style.position = 'fixed';
    overlay2.style.top = '0';
    overlay2.style.left = '0';
    overlay2.style.width = '100%';
    overlay2.style.height = '100%';
    overlay2.style.zIndex = '9999'; // 确保遮罩层在最上层显示

    // 创建iframe2元素
    const iframe2 = document.createElement('iframe');
    iframe2.src = url2;
    iframe2.style.display = 'block';
    iframe2.style.width = '650px';
    iframe2.style.height = '680px';
    // iframe2.style.backgroundColor = 'white';
    iframe2.style.border = 'none';
    iframe2.style.margin = 'auto';
    iframe2.style.position = 'absolute';
    iframe2.style.top = '50%';
    iframe2.style.left = '50%';
    iframe2.style.transform = 'translate(-50%, -50%)'; // 居中显示
    // 给 iframe 添加 ID
    iframe2.id = 'myIframe';

    // 将iframe2添加到遮罩层中
    overlay2.appendChild(iframe2);

    // 将遮罩层添加到页面中
    document.body.appendChild(overlay2);

    // 等待iframe加载完毕
    iframe2.onload = function () {

        let iframeDocument2 = iframe2.contentWindow.document;
        let iframeWindow2 = iframe2.contentWindow;

        const Button_back = iframeDocument2.getElementById('Btn_Back');

        // 通过 ID 获取 iframe 元素
        const myIframe = document.getElementById('myIframe');

        // 修改 iframe 的宽高
        myIframe.style.width = '100%';
        myIframe.style.height = '100%';

        if (Button_back) {
            // 绑定Button_back点击事件
            Button_back.addEventListener('click', function () {
                // 清理iframe内部资源
                iframe2.src = 'about:blank';
                // 移除遮罩层
                overlay2.remove();
            })
        }
    }
}
// 查询其他格式GLTF FBX 3DS X STL转换状态
function GetExportClassBtn(ID) {
    // GLTF
    const Button_exportgltf = iframeDocument.getElementById('Export_gltf');

    // 查询gltf格式转换状态
    var gltf = Get_SQLData_ExportClassStateByID(ID, "gltf");
    // 激活gltf按钮
    iframeWindow.ExportGLTFFinish();

    // 使用 then 方法处理异步操作结果
    gltf.then(result => {
        if (result) {
            // 下载模型事件
            if (Button_exportgltf) {
                // 转换完成后设置为可点击
                Button_exportgltf.innerHTML = 'GLTF';
                Button_exportgltf.disabled = false;
                Button_exportgltf.addEventListener('click', () => {
                    // 设置按钮的链接和下载属性
                    let fileUrl = updata_http + "uploads/" + ID + '/gltf_' + ID + '.zip';
                    let a = document.createElement('a');
                    a.href = fileUrl;
                    a.download = 'file.pdf'; // 设置下载的文件名
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                });
            }

        } else {
            // 添加class样式
            Button_exportgltf.classList.add('button_convert');

            // 绑定执行转换任务
            Button_exportgltf.addEventListener('click', function () {
                ExportFormatTask(ID, "gltf");
                // 点击后状态设置为不可点击
                Button_exportgltf.innerHTML = 'Loading';
                Button_exportgltf.disabled = true;
            });
        }
    });

    // FBX
    const Button_exportfbx = iframeDocument.getElementById('Export_fbx');

    // 查询fbx格式转换状态
    var fbx = Get_SQLData_ExportClassStateByID(ID, "fbx");
    // 激活fbx按钮
    iframeWindow.ExportFBXFinish();

    // 使用 then 方法处理异步操作结果
    fbx.then(result => {
        if (result) {
            // 下载模型事件
            if (Button_exportfbx) {
                // 转换完成后设置为可点击
                Button_exportfbx.innerHTML = 'FBX';
                Button_exportfbx.disabled = false;
                Button_exportfbx.addEventListener('click', () => {
                    // 设置按钮的链接和下载属性
                    let fileUrl = updata_http + "uploads/" + ID + '/fbx_' + ID + '.zip';
                    let a = document.createElement('a');
                    a.href = fileUrl;
                    a.download = 'file.pdf'; // 设置下载的文件名
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                });
            }

        } else {
            // 添加class样式
            Button_exportfbx.classList.add('button_convert');

            // 绑定执行转换任务
            Button_exportfbx.addEventListener('click', function () {
                ExportFormatTask(ID, "fbx");
                // 点击后状态设置为不可点击
                Button_exportfbx.innerHTML = 'Loading';
                Button_exportfbx.disabled = true;
            });
        }
    });

    // 3DS
    const Button_export3ds = iframeDocument.getElementById('Export_3ds');

    // 查询3ds格式转换状态
    var _3ds = Get_SQLData_ExportClassStateByID(ID, "3ds");
    // 激活3ds按钮
    iframeWindow.Export3DSFinish();

    // 使用 then 方法处理异步操作结果
    _3ds.then(result => {
        if (result) {
            // 下载模型事件
            if (Button_export3ds) {
                // 转换完成后设置为可点击
                Button_export3ds.innerHTML = '3DS';
                Button_export3ds.disabled = false;
                Button_export3ds.addEventListener('click', () => {
                    // 设置按钮的链接和下载属性
                    let fileUrl = updata_http + "uploads/" + ID + '/3ds_' + ID + '.zip';
                    let a = document.createElement('a');
                    a.href = fileUrl;
                    console.log(fileUrl);
                    a.download = 'file.pdf'; // 设置下载的文件名
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                });
            }

        } else {
            // 添加class样式
            Button_export3ds.classList.add('button_convert');

            // 绑定执行转换任务
            Button_export3ds.addEventListener('click', function () {
                ExportFormatTask(ID, "3ds");
                // 点击后状态设置为不可点击
                Button_export3ds.innerHTML = 'Loading';
                Button_export3ds.disabled = true;
            });
        }
    });

    // X
    const Button_exportX = iframeDocument.getElementById('Export_x');

    // 查询3ds格式转换状态
    var _x = Get_SQLData_ExportClassStateByID(ID, "x");
    // 激活3ds按钮
    iframeWindow.ExportXFinish();

    // 使用 then 方法处理异步操作结果
    _x.then(result => {
        if (result) {
            // 下载模型事件
            if (Button_exportX) {
                // 转换完成后设置为可点击
                Button_exportX.innerHTML = 'X';
                Button_exportX.disabled = false;
                Button_exportX.addEventListener('click', () => {
                    // 设置按钮的链接和下载属性
                    let fileUrl = updata_http + "uploads/" + ID + '/x_' + ID + '.zip';
                    let a = document.createElement('a');
                    a.href = fileUrl;
                    a.download = 'file.pdf'; // 设置下载的文件名
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                });
            }

        } else {
            // 添加class样式
            Button_exportX.classList.add('button_convert');

            // 绑定执行转换任务
            Button_exportX.addEventListener('click', function () {
                ExportFormatTask(ID, "x");
                // 点击后状态设置为不可点击
                Button_exportX.innerHTML = 'Loading';
                Button_exportX.disabled = true;
            });
        }
    });

    // STL
    const Button_exportSTL = iframeDocument.getElementById('Export_stl');

    // 查询3ds格式转换状态
    var _stl = Get_SQLData_ExportClassStateByID(ID, "stl");
    // 激活3ds按钮
    iframeWindow.ExportSTLFinish();

    // 使用 then 方法处理异步操作结果
    _stl.then(result => {
        if (result) {
            // 下载模型事件
            if (Button_exportSTL) {
                // 转换完成后设置为可点击
                Button_exportSTL.innerHTML = 'STL';
                Button_exportSTL.disabled = false;
                Button_exportSTL.addEventListener('click', () => {
                    // 设置按钮的链接和下载属性
                    let fileUrl = updata_http + "uploads/" + ID + '/stl_' + ID + '.zip';
                    let a = document.createElement('a');
                    a.href = fileUrl;
                    a.download = 'file.pdf'; // 设置下载的文件名
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                });
            }

        } else {
            // 添加class样式
            Button_exportSTL.classList.add('button_convert');

            // 绑定执行转换任务
            Button_exportSTL.addEventListener('click', function () {
                ExportFormatTask(ID, "stl");
                // 点击后状态设置为不可点击
                Button_exportSTL.innerHTML = 'Loading';
                Button_exportSTL.disabled = true;
            });
        }
    });

}

// 根据ID请求执行ExportTask任务
function ExportTask(ID) {
    // 指定API的URL
    const apiUrl = ClientServer_URL + "/ExportTask";
    // 构造请求对象
    var requestOptions = {
        method: 'POST',  // 或者 'GET'，取决于你的后端路由
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ id: ID })
    };
    // 发送fetch请求
    fetch(apiUrl, requestOptions)
        .then(response => response.json())
        .then(data => {
            console.log('成功收到响应:', data);
            // 在这里处理后端的响应
            // 执行ExorptOBJ查询
            Get_SQLData_ExportOBJ_ProgressByID(ID)
        })
        .catch(error => {
            console.error('发生错误:', error);
        });
}

// 根据ID请求执行ExportGLTF任务
function ExportFormatTask(ID, FORMAT) {
    // 指定API的URL
    const apiUrl = ClientServer_URL + "/ExportFormatTask";
    // 构造请求对象
    var requestOptions = {
        method: 'POST',  // 或者 'GET'，取决于你的后端路由
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ id: ID, type: FORMAT })
    };
    // 发送fetch请求
    fetch(apiUrl, requestOptions)
        .then(response => response.json())
        .then(data => {
            console.log('成功收到响应:', data);
            switch (FORMAT) {
                case 'gltf':
                    // 查询gltf格式转换状态
                    GetSqlData_ExportClassGltf(ID);
                    break;
                case 'fbx':
                    // 查询fbx格式转换状态
                    GetSqlData_ExportClassFbx(ID);
                    break;
                case '3ds':
                    // 查询3ds格式转换状态
                    GetSqlData_ExportClass3ds(ID);
                    break;
                case 'x':
                    // 查询x格式转换状态
                    GetSqlData_ExportClassX(ID);
                    break;
                case 'stl':
                    // 查询stl格式转换状态
                    GetSqlData_ExportClassStl(ID);
                    break;
                default:
                    console.log('Unknown format');
            }
        })
        .catch(error => {
            console.error('发生错误:', error);
        });
}

// 轮询GLTF转换状态
function GetSqlData_ExportClassGltf(ID) {
    // 查询gltf格式转换状态
    var _gltf = Get_SQLData_ExportClassStateByID(ID, "gltf");
    // 获取按钮元素
    const Button_exportgltf = iframeDocument.getElementById('Export_gltf');

    _gltf.then(result => {
        if (result) {

            // 移除class样式
            Button_exportgltf.classList.remove('button_convert');

            // 下载模型事件
            if (Button_exportgltf) {
                // 转换完成后设置为可点击
                Button_exportgltf.innerHTML = 'GLTF';
                Button_exportgltf.disabled = false;
                Button_exportgltf.addEventListener('click', () => {
                    // 设置按钮的链接和下载属性
                    let fileUrl = updata_http + "uploads/" + ID + '/gltf_' + ID + '.zip';
                    let a = document.createElement('a');
                    a.href = fileUrl;
                    a.download = 'file.pdf'; // 设置下载的文件名
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                });

                // 执行下载
                let fileUrl = updata_http + "uploads/" + ID + '/gltf_' + ID + '.zip';
                let a = document.createElement('a');
                a.href = fileUrl;
                a.download = 'file.pdf'; // 设置下载的文件名
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
            }

        } else {
            // 点击后状态设置为不可点击
            Button_exportgltf.innerHTML = 'Loading';
            Button_exportgltf.disabled = true;
            // 2秒后执行轮询
            setTimeout(() => GetSqlData_ExportClassGltf(ID), 2000);
        }
    });
}

// 轮询FBX转换状态
function GetSqlData_ExportClassFbx(ID) {
    // 查询fbx格式转换状态
    var _fbx = Get_SQLData_ExportClassStateByID(ID, "fbx");
    // 获取按钮元素
    const Button_exportfbx = iframeDocument.getElementById('Export_fbx');

    _fbx.then(result => {
        if (result) {

            // 移除class样式
            Button_exportfbx.classList.remove('button_convert');

            // 下载模型事件
            if (Button_exportfbx) {
                // 转换完成后设置为可点击
                Button_exportfbx.innerHTML = 'FBX';
                Button_exportfbx.disabled = false;
                Button_exportfbx.addEventListener('click', () => {
                    // 设置按钮的链接和下载属性
                    let fileUrl = updata_http + "uploads/" + ID + '/fbx_' + ID + '.zip';
                    let a = document.createElement('a');
                    a.href = fileUrl;
                    a.download = 'file.pdf'; // 设置下载的文件名
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                });

                // 执行下载
                let fileUrl = updata_http + "uploads/" + ID + '/fbx_' + ID + '.zip';
                let a = document.createElement('a');
                a.href = fileUrl;
                a.download = 'file.pdf'; // 设置下载的文件名
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
            }

        } else {
            // 点击后状态设置为不可点击
            Button_exportfbx.innerHTML = 'Loading';
            Button_exportfbx.disabled = true;
            // 2秒后执行轮询
            setTimeout(() => GetSqlData_ExportClassFbx(ID), 2000);
        }
    });
}

// 轮询3DS转换状态
function GetSqlData_ExportClass3ds(ID) {
    // 查询3ds格式转换状态
    var _3ds = Get_SQLData_ExportClassStateByID(ID, "3ds");
    // 获取按钮元素
    const Button_export3ds = iframeDocument.getElementById('Export_3ds');

    _3ds.then(result => {
        if (result) {

            // 移除class样式
            Button_export3ds.classList.remove('button_convert');

            // 下载模型事件
            if (Button_export3ds) {
                // 转换完成后设置为可点击
                Button_export3ds.innerHTML = '3DS';
                Button_export3ds.disabled = false;
                Button_export3ds.addEventListener('click', () => {
                    // 设置按钮的链接和下载属性
                    let fileUrl = updata_http + "uploads/" + ID + '/3ds_' + ID + '.zip';
                    let a = document.createElement('a');
                    a.href = fileUrl;
                    a.download = 'file.pdf'; // 设置下载的文件名
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                });

                // 执行下载
                let fileUrl = updata_http + "uploads/" + ID + '/3ds_' + ID + '.zip';
                let a = document.createElement('a');
                a.href = fileUrl;
                a.download = 'file.pdf'; // 设置下载的文件名
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
            }

        } else {
            // 点击后状态设置为不可点击
            Button_export3ds.innerHTML = 'Loading';
            Button_export3ds.disabled = true;
            // 2秒后执行轮询
            setTimeout(() => GetSqlData_ExportClass3ds(ID), 2000);
        }
    });
}

// 轮询X转换状态
function GetSqlData_ExportClassX(ID) {
    // 查询X格式转换状态
    var _x = Get_SQLData_ExportClassStateByID(ID, "x");
    // 获取按钮元素
    const Button_exportX = iframeDocument.getElementById('Export_x');
    _x.then(result => {
        if (result) {

            // 移除class样式
            Button_exportX.classList.remove('button_convert');

            // 下载模型事件
            if (Button_exportX) {
                // 转换完成后设置为可点击
                Button_exportX.innerHTML = 'X';
                Button_exportX.disabled = false;
                Button_exportX.addEventListener('click', () => {
                    // 设置按钮的链接和下载属性
                    let fileUrl = updata_http + "uploads/" + ID + '/x_' + ID + '.zip';
                    let a = document.createElement('a');
                    a.href = fileUrl;
                    a.download = 'file.pdf'; // 设置下载的文件名
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                });

                // 执行下载
                let fileUrl = updata_http + "uploads/" + ID + '/x_' + ID + '.zip';
                let a = document.createElement('a');
                a.href = fileUrl;
                a.download = 'file.pdf'; // 设置下载的文件名
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
            }

        } else {
            // 点击后状态设置为不可点击
            Button_exportX.innerHTML = 'Loading';
            Button_exportX.disabled = true;
            // 2秒后执行轮询
            setTimeout(() => GetSqlData_ExportClassX(ID), 2000);
        }
    });
}

// 轮询STL转换状态
function GetSqlData_ExportClassStl(ID) {
    // 查询3ds格式转换状态
    var _stl = Get_SQLData_ExportClassStateByID(ID, "stl");
    // 获取按钮元素
    const Button_exportSTL = iframeDocument.getElementById('Export_stl');

    _stl.then(result => {
        if (result) {

            // 移除class样式
            Button_exportSTL.classList.remove('button_convert');

            // 下载模型事件
            if (Button_exportSTL) {
                // 转换完成后设置为可点击
                Button_exportSTL.innerHTML = 'STL';
                Button_exportSTL.disabled = false;
                Button_exportSTL.addEventListener('click', () => {
                    // 设置按钮的链接和下载属性
                    let fileUrl = updata_http + "uploads/" + ID + '/stl_' + ID + '.zip';
                    let a = document.createElement('a');
                    a.href = fileUrl;
                    a.download = 'file.pdf'; // 设置下载的文件名
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                });

                // 执行下载
                let fileUrl = updata_http + "uploads/" + ID + '/stl_' + ID + '.zip';
                let a = document.createElement('a');
                a.href = fileUrl;
                a.download = 'file.pdf'; // 设置下载的文件名
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
            }

        } else {
            // 点击后状态设置为不可点击
            Button_exportSTL.innerHTML = 'Loading';
            Button_exportSTL.disabled = true;
            // 2秒后执行轮询
            setTimeout(() => GetSqlData_ExportClassStl(ID), 2000);
        }
    });
}

// 根据ID请求本地数据库上的OBJ转换状态
function Get_SQLData_OBJ_ByID(ID) {
    // 指定API的URL
    const apiUrl = ClientServer_URL + "get_ExportOBJByID";

    // 构建包含ID参数的请求体
    const requestBody = {
        id: ID,
    };

    // 使用Fetch API进行POST请求
    fetch(apiUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
    })
        .then(response => {
            // 检查请求是否成功
            if (!response.ok) {
                throw new Error(`Network response was not ok: ${response.status}`);
            }
            // 将响应解析为JSON
            return response.json();
        })
        .then(data => {
            // 解析message字段中的JSON字符串
            var messageObject = JSON.parse(data.message);

            // 处理获取到的数据
            if (data.status === 'success') {
                const progress = messageObject.export_obj_progress;
                const finish = messageObject.export_obj_state;
                let Button_exportOBJ = iframeWindow.document.getElementById('Export_obj');

                // 判断当前任务如果未完成且未开始训练
                if (!finish && progress == 0) {
                    // console.log(1);
                    // 根据ID请求执行ExportTask任务 已改为后端直接自动执行

                    // 添加灰色可点击状态lass样式
                    Button_exportOBJ.classList.add('button_convert');
                    // 将OBJ按钮设为可用状态
                    iframeWindow.ExportOBJFinish();

                    // 执行Nerf2Mesh
                    if (Button_exportOBJ) {
                        Button_exportOBJ.addEventListener('click', () => {
                            ExportTask(ID);
                        });
                    }

                    // 执行ExorptOBJ查询
                    // Get_SQLData_ExportOBJ_ProgressByID(ID)
                    return true;
                    // 判断如果任务完成了且进度为100
                } else if (finish && progress == 100) {
                    // console.log(3);                    
                    // 移除class样式
                    Button_exportOBJ.classList.remove('button_convert');
                    // 将OBJ按钮设为可用状态
                    iframeWindow.ExportOBJFinish();

                    // 下载OBJ模型事件
                    if (Button_exportOBJ) {
                        Button_exportOBJ.addEventListener('click', () => {
                            console.log("ExportOBJ");
                            // 设置按钮的链接和下载属性
                            let fileUrl = updata_http + "uploads/" + ID + "/OBJ_" + ID + ".zip";
                            let a = document.createElement('a');
                            a.href = fileUrl;
                            a.download = 'file.pdf'; // 设置下载的文件名
                            document.body.appendChild(a);
                            a.click();
                            document.body.removeChild(a);
                        });
                    }

                    // 检测其他的按钮状态
                    GetExportClassBtn(ID);
                    return false;
                    // 判断当前任务完成了或已经开始训练了
                } else if (finish || progress != 0) {
                    // console.log(2);
                    Get_SQLData_ExportOBJ_ProgressByID(ID);
                    return false;
                }
            } else {
                // 处理服务器返回的错误消息
                console.error('Server error:', data.message);
                return false;
            }
        })
        .catch(error => {
            // 处理错误
            console.error('Fetch error:', error);
            return false;
        });
}

// 根据ID请求本地数据库上的NeRF训练进度
function Get_SQLData_NeRF_ProgressByID(ID) {
    // console.log("GPU_ProgressByID");
    // 指定API的URL
    const apiUrl = ClientServer_URL + "get_NerfByID";

    // 构建包含ID参数的请求体
    const requestBody = {
        id: ID,
    };

    // 使用Fetch API进行POST请求
    fetch(apiUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
    })
        .then(response => {
            // 检查请求是否成功
            if (!response.ok) {
                throw new Error(`Network response was not ok: ${response.status}`);
            }
            // 将响应解析为JSON
            return response.json();
        })
        .then(data => {
            // 解析message字段中的JSON字符串
            var messageObject = JSON.parse(data.message);

            // 处理获取到的数据
            if (data.status === 'success') {
                const progress = messageObject.nerfacto_progress;
                const finish = messageObject.nerfacto_status;
                let Button_exportOBJ = iframeWindow.document.getElementById('Export_obj');

                // 判断当前任务训练是否完成
                if (finish) {
                    // 停止轮询
                    console.log("执行完毕");
                    iframeWindow.NerfFinish();

                    // 获取OBJ转换进度 - 改为手动点击OBJ
                    // Get_SQLData_OBJ_ByID(ID)

                    // 添加灰色可点击状态lass样式
                    Button_exportOBJ.classList.add('button_convert');
                    // 将OBJ按钮设为可用状态
                    iframeWindow.ExportOBJFinish();

                    // 执行Nerf2Mesh
                    if (Button_exportOBJ) {
                        Button_exportOBJ.addEventListener('click', () => {
                            ExportTask(ID);
                        });
                    }

                } else {
                    // console.log(progress);
                    iframeWindow.updataProgress(progress);

                    // 设置计时器并将标识符存储在 timerId 中
                    timerId = setTimeout(() => Get_SQLData_NeRF_ProgressByID(ID), 2000);
                }
            } else {
                // 处理服务器返回的错误消息
                console.error('Server error:', data.message);
            }
        })
        .catch(error => {
            // 处理错误
            console.error('Fetch error:', error);
        });

}

// 根据ID请求本地数据库上的ExportOBJ训练进度
function Get_SQLData_ExportOBJ_ProgressByID(ID) {
    // console.log("GPU_ProgressByID");
    // 指定API的URL
    const apiUrl = ClientServer_URL + "get_ExportOBJByID";

    // 构建包含ID参数的请求体
    const requestBody = {
        id: ID,
    };

    // 使用Fetch API进行POST请求
    fetch(apiUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
    })
        .then(response => {
            // 检查请求是否成功
            if (!response.ok) {
                throw new Error(`Network response was not ok: ${response.status}`);
            }
            // 将响应解析为JSON
            return response.json();
        })
        .then(data => {
            // 解析message字段中的JSON字符串
            var messageObject = JSON.parse(data.message);

            // 处理获取到的数据
            if (data.status === 'success') {
                const progress = messageObject.export_obj_progress;
                const finish = messageObject.export_obj_state;
                let Button_exportOBJ = iframeWindow.document.getElementById('Export_obj');

                // 判断当前任务训练是否完成
                if (finish) {
                    // 停止轮询
                    console.log("执行完毕");
                    iframeWindow.ExportOBJProgress(100);

                    // 移除class样式
                    Button_exportOBJ.classList.remove('button_convert');

                    // 将OBJ按钮设为可用状态
                    iframeWindow.ExportOBJFinish();

                    // 下载OBJ模型事件
                    if (Button_exportOBJ) {
                        Button_exportOBJ.addEventListener('click', () => {
                            console.log("ExportOBJ");
                            // 设置按钮的链接和下载属性
                            let fileUrl = updata_http + "uploads/" + ID + "/OBJ_" + ID + ".zip";
                            let a = document.createElement('a');
                            a.href = fileUrl;
                            a.download = 'file.pdf'; // 设置下载的文件名
                            document.body.appendChild(a);
                            a.click();
                            document.body.removeChild(a);
                        });
                    }

                } else {
                    iframeWindow.ExportOBJProgress(progress);
                    // 2秒后执行轮询
                    timerOBJ = setTimeout(() => Get_SQLData_ExportOBJ_ProgressByID(ID), 2000);
                }
            } else {
                // 处理服务器返回的错误消息
                console.error('Server error:', data.message);
            }
        })
        .catch(error => {
            // 处理错误
            console.error('Fetch error:', error);
        });

}

// 根据ID请求本地数据库上的Export格式状态
function Get_SQLData_ExportClassStateByID(ID, TYPE) {
    const apiUrl = ClientServer_URL + "get_ExportClassByID";

    const requestBody = {
        project_name: ID,
        export_type: TYPE
    };

    return new Promise((resolve, reject) => {
        fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody),
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Network response was not ok: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    const messageObject = JSON.parse(data.message);
                    const finish = messageObject.export_Class_state;
                    resolve(finish === 1);
                } else {
                    resolve(false);
                }
            })
            .catch(error => {
                console.error('Request failed:', error);
                resolve(false);
            });
    });
}

// 根据ID请求GPUWork上的训练进度
function Get_GPU_ProgressByID(ProgressElement, ID) {
    // console.log("GPU_ProgressByID");
    // 指定API的URL
    const apiUrl = GPU_Manager_URL + "Get_ProgressByID";

    // 构建包含ID参数的请求体
    const requestBody = {
        id: ID,
    };

    // 使用Fetch API进行POST请求
    fetch(apiUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
    })
        .then(response => {
            // 检查请求是否成功
            if (!response.ok) {
                throw new Error(`Network response was not ok: ${response.status}`);
            }
            // 将响应解析为JSON
            return response.json();
        })
        .then(data => {
            // 解析message字段中的JSON字符串
            var messageObject = JSON.parse(data.message);

            // 处理获取到的数据
            if (data.status === 'success') {
                const progress = messageObject.Progress;
                const status = messageObject.Status;
                const finish = messageObject.Finish;

                // 判断当前任务训练是否完成
                if (finish) {
                    // 检查是否已经执行过相同ID的代码
                    if (FinishIDs.includes(ID)) {
                        // console.log('ID:', ID, '的代码已执行过，跳过。');
                        return;
                    }
                    // 添加ID到已执行集合
                    FinishIDs.push(ID);
                    // 根据ID设置[本地]数据库项目状态
                    // 20240228修改为运算平台主动更新
                    // SetPrjStatusByID(ID)
                    // 停止轮询
                    stopEvent(ID)
                } else {
                    ProgressElement.innerHTML = progress;
                    if (progress != "Queue") {
                        // 更新进度到本地数据库
                        // 20240228修改为运算平台主动更新
                        // SetPrjProgressByID(ID, progress);
                        // 检查是否已经执行过相同ID的代码
                        if (executedIDs.includes(ID)) {
                            // console.log('ID:', ID, '的代码已执行过，跳过。');
                            return;
                        }
                        // 添加ID到已执行集合
                        executedIDs.push(ID);
                        // 设置加载封面
                        var Elements_project = document.getElementsByClassName(ID)[0];

                        // 获取图片元素
                        var childElements_Proj = Elements_project.getElementsByClassName('ListImg')[0];

                        if (childElements_Proj) {
                            // 设置图片内容
                            // childElements_Proj.style.background = "url('" + updata_http + "uploads/" + ID + "/sfm/images_4/frame_00001.png') center / cover";
                            // 设置新的图像源路径 20240426
                            childElements_Proj.setAttribute('src', updata_http + "uploads/" + ID + "/sfm/images_4/frame_00001.png");
                            // 设置图片高斯
                            childElements_Proj.style.filter = "blur(3px)";
                        }

                    }
                }
            } else {
                // 处理服务器返回的错误消息
                console.error('Server error:', data.message);
            }
        })
        .catch(error => {
            // 处理错误
            console.error('Fetch error:', error);
        });

}

// 根据ID请求本地数据库上的训练进度
function Get_SQLData_ProgressByID(ProgressElement, ID) {
    // console.log("GPU_ProgressByID");
    // 指定API的URL
    const apiUrl = ClientServer_URL + "get_dataByID";

    // 构建包含ID参数的请求体
    const requestBody = {
        id: ID,
    };

    // 使用Fetch API进行POST请求
    fetch(apiUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
    })
        .then(response => {
            // 检查请求是否成功
            if (!response.ok) {
                throw new Error(`Network response was not ok: ${response.status}`);
            }
            // 将响应解析为JSON
            return response.json();
        })
        .then(data => {
            // 解析message字段中的JSON字符串
            var messageObject = JSON.parse(data.message);

            // 处理获取到的数据
            if (data.status === 'success') {
                const progress = messageObject.project_progress;
                const finish = messageObject.project_state;

                // 判断当前任务训练是否完成
                if (finish) {
                    // 检查是否已经执行过相同ID的代码
                    if (FinishIDs.includes(ID)) {
                        // console.log('ID:', ID, '的代码已执行过，跳过。');
                        return;
                    }
                    // 添加ID到已执行集合
                    FinishIDs.push(ID);
                    // 根据ID设置[本地]数据库项目状态
                    // 20240228修改为运算平台主动更新
                    // SetPrjStatusByID(ID)
                    // 停止轮询
                    stopEvent(ID)
                } else {
                    ProgressElement.innerHTML = progress;
                    if (progress != "Queue") {
                        // 更新进度到本地数据库
                        // 20240228修改为运算平台主动更新
                        // SetPrjProgressByID(ID, progress);
                        // 检查是否已经执行过相同ID的代码
                        if (executedIDs.includes(ID)) {
                            // console.log('ID:', ID, '的代码已执行过，跳过。');
                            return;
                        }
                        // 添加ID到已执行集合
                        executedIDs.push(ID);
                        // 设置加载封面
                        var Elements_project = document.getElementsByClassName(ID)[0];
                        // 获取图片元素
                        var childElements_Proj = Elements_project.getElementsByClassName('ListImg')[0];

                        if (childElements_Proj) {
                            // 设置图片内容
                            // childElements_Proj.style.background = "url('" + updata_http + "uploads/" + ID + "/sfm/images_4/frame_00001.png') center / cover";
                            // 设置新的图像源路径 20240426
                            childElements_Proj.setAttribute('src', updata_http + "uploads/" + ID + "/sfm/images_4/frame_00001.png");
                            // 设置图片高斯
                            childElements_Proj.style.filter = "blur(3px)";
                        }

                    }
                }
            } else {
                // 处理服务器返回的错误消息
                console.error('Server error:', data.message);
            }
        })
        .catch(error => {
            // 处理错误
            console.error('Fetch error:', error);
        });

}

// 根据ID查找数据库训练进度
function progressByID(ProgressElement, ID) {
    // 构造请求对象
    var requestOptions = {
        method: 'POST',  // 或者 'GET'，取决于你的后端路由
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ id: ID })
    };

    // 发送fetch请求
    fetch('/get_dataByID', requestOptions)
        .then(response => response.json())
        .then(data => {
            // console.log('成功收到响应:', data);
            // 在这里处理后端的响应
            // 解析message字段中的JSON字符串
            var messageObject = JSON.parse(data.message);
            const project_progress = messageObject.project_progress;
            const project_state = messageObject.project_state;
            // 判断当前任务训练是否完成
            if (project_state) {
                stopEvent(ID)
            } else {
                ProgressElement.innerHTML = project_progress;
            }
        })
        .catch(error => {
            console.error('发生错误:', error);
        });
}

// 更新[本地]数据库 指定ID训练状态为完成
function SetPrjStatusByID(ID) {
    // 构造请求对象
    var requestOptions = {
        method: 'POST',  // 或者 'GET'，取决于你的后端路由
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ id: ID })
    };

    // 发送fetch请求
    fetch('/updataProjectState', requestOptions)
        .then(response => response.json())
        .then(data => {
            // 解析message字段中的JSON字符串
            // var messageObject = JSON.parse(data.message);
            // console.log(messageObject);

        })
        .catch(error => {
            console.error('发生错误:', error);
        });
}

// 根据ID更新进度状态到[本地]数据库
function SetPrjProgressByID(ID, progress) {
    // 构造请求对象
    var requestOptions = {
        method: 'POST',  // 或者 'GET'，取决于你的后端路由
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ id: ID, progressVal: progress })
    };

    // 发送fetch请求
    fetch('/updataProjectProgress', requestOptions)
        .then(response => response.json())
        .then(data => {
            // 解析message字段中的JSON字符串
            // var messageObject = JSON.parse(data.message);
            // console.log(messageObject);
            // console.log(progress)

        })
        .catch(error => {
            console.error('发生错误:', error);
        });
}


// 执行视频处理事件
function run_convert(folder_path, file_path, folder_name) {
    // 构造请求对象
    var requestOptions = {
        method: 'POST',  // 或者 'GET'，取决于你的后端路由
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ "folder_path": folder_path, "file_path": file_path, "folder_name": folder_name })
    };

    // 发送fetch请求
    fetch('/run_convert', requestOptions)
        .then(response => response.json())
        .then(data => {
            console.log('成功收到响应:', data);
            // 在这里处理后端的响应        
        })
        .catch(error => {
            console.error('发生错误:', error);
        });
}

// 刷新列表状态
function reashListState() {
    const thumbnails = document.querySelectorAll('.thumbnail');

    thumbnails.forEach(thumbnail => {
        const status = thumbnail.getAttribute('data-status');
        const loadingIndicator = thumbnail.querySelector('.thumbnail-loading');
        const buttons = thumbnail.querySelector('.thumbnail-buttons');
        const link = thumbnail.querySelector('.thumbnail-link');

        if (status === 'loading') {
            thumbnail.classList.add('calculating');
            loadingIndicator.classList.remove('hidden');
            buttons.classList.add('hidden');
            link.classList.add('pointer-events-none');
        } else {
            thumbnail.classList.remove('calculating');
            loadingIndicator.classList.add('hidden');
            buttons.classList.remove('hidden');
            link.classList.remove('pointer-events-none');
        }
    });
    // 刷新icon图标
    feather.replace();
}

// 底部弹出提示通知
function notification() {
    const notification = document.getElementById('notification');

    // 显示通知窗口并设置定时器自动隐藏
    function showNotification(message, duration) {
        // 设置通知文本
        notification.textContent = message;
        // 显示通知窗口
        notification.classList.remove('translate-y-full');
        // 定时隐藏通知窗口
        setTimeout(function () {
            hideNotification();
        }, duration);
    }

    // 隐藏通知窗口
    function hideNotification() {
        // 隐藏通知窗口
        notification.classList.add('translate-y-full');
    }

    // 在页面加载后调用 showNotification 函数显示通知
    // 第一个参数为要显示的消息内容，第二个参数为通知窗口显示的时间（毫秒）
    showNotification('No captures found!', 2000);
}

// 页面加载时触发 'get_data' 事件，请求数据
document.addEventListener('DOMContentLoaded', function () {

    // 从服务器获取数据
    get_data_from_serve();

    // 获取输入框元素
    const searchInput = document.getElementById('searchInput');

    // 监听输入框的 keydown 事件
    searchInput.addEventListener('keydown', function (event) {
        // 检查按下的键是否是回车键（keyCode为13）
        if (event.keyCode === 13) {
            // 获取输入框的值
            const search = searchInput.value.trim();
            // 调用 searchList 函数
            searchList(search);
        }
    });

    // 下拉Menu
    const userBtn = document.getElementById('userBtn');
    const userDropdown = document.getElementById('userDropdown');
    const menuBtn = document.getElementById('menuBtn');
    const menuDropdown = document.getElementById('menuDropdown');

    if (userBtn) {
        userBtn.addEventListener('click', () => {
            userDropdown.classList.toggle('hidden');
            menuDropdown.classList.add('hidden');
        });
    }

    if (menuBtn) {
        menuBtn.addEventListener('click', () => {
            menuDropdown.classList.toggle('hidden');
            userDropdown.classList.add('hidden');
        });
    }

    // 点击其他区域关闭下拉菜单
    document.addEventListener('click', (event) => {
        const isClickInsideUserDropdown = userDropdown.contains(event.target);
        const isClickInsideUserBtn = userBtn.contains(event.target);
        const isClickInsideMenuDropdown = menuDropdown.contains(event.target);
        const isClickInsideMenuBtn = menuBtn.contains(event.target);

        if (!isClickInsideUserDropdown && !isClickInsideUserBtn) {
            userDropdown.classList.add('hidden');
        }

        if (!isClickInsideMenuDropdown && !isClickInsideMenuBtn) {
            menuDropdown.classList.add('hidden');
        }
    });

});