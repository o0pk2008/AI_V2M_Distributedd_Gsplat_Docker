
import * as THREE from 'three';

import Stats from 'three/addons/libs/stats.module.js';
import { PLYLoader } from 'three/addons/loaders/PLYLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { TransformControls } from 'three/addons/controls/TransformControls2.js';

// 获取地址栏中的参数
const urlParams = new URLSearchParams(window.location.search);
const idKey = urlParams.get('idkey');
const ClientServer_URL = urlParams.get('serveIP');
const updata_http = urlParams.get('updata_http');

var timerOBJ;

// 导出模型按钮
var btnExportMesh;

// 创建场景
let camera, scene, renderer;

// 添加鼠标控制
let controls;

// 创建六面体
let planes = [];
let cones = [];
let planeSize = 4;
let planeGeometry = new THREE.PlaneGeometry(0.05, 0.05);
let planeColors = [0xff0000, 0x00ff00, 0x0000ff, 0xffff00, 0xff00ff, 0x00ffff];
let coneLength = 0.1;
let coneRadius = 0.04;
let coneColor = 0x03e889;

// 边界框
let boundingBox = null;
let boundingBoxcenter = new THREE.Vector3();
let boundingBoxScale = new THREE.Vector3();
let boundingBoxRotation = new THREE.Vector3();

// 蓝色BoxMesh
let boundingBoxMesh;

// 拖拽平面
let planeBeingDragged = null;
let initialMousePosition = new THREE.Vector3();
let initialPlanePosition = new THREE.Vector3();

// 点云geometry
let geometry_PLY;
let geometry_PLY_Reset;
let transformControls = []; // 创建一个数组来存储每个平面对应的 TransformControl

let originalPositions = [];
let originalColors = [];

// 请求[客户端]数据库裁剪矩阵
async function fetchCropData(param_id) {
    const url = ClientServer_URL + '/get_crop_position_and_scale';
    const data = { id: param_id };

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const responseData = await response.json();

        if (responseData.status === 'success' && responseData.message) {
            const message = JSON.parse(responseData.message);
            const CropPositionArray = message.CropPosition.split(',').map(parseFloat);
            const CropScaleArray = message.CropScale.split(',').map(parseFloat);
            const CropRotationArray = message.CropRotation.split(',').map(parseFloat);

            const CropPosition = new THREE.Vector3(...CropPositionArray);
            const CropScale = new THREE.Vector3(...CropScaleArray);
            const CropRotation = new THREE.Vector3(...CropRotationArray);

            return { CropPosition, CropScale, CropRotation };
        } else {
            throw new Error('No valid data in the response');
        }
    } catch (error) {
        console.error('There was a problem with the fetch operation:', error);
        return null;
    }
}

function convertJSONToFormat(jsonStr) {
    // 解析 JSON 字符串
    const jsonObj = JSON.parse(jsonStr);

    // 提取属性值并拼接成所需格式的字符串
    const formattedStr = `${jsonObj.x}, ${jsonObj.y}, ${jsonObj.z}`;

    return formattedStr;
}

// 写入裁剪矩阵到[客户端]数据库
function updateCropPositionAndScale(CropPositionArray, CropScaleArray, CropRotationArray, id) {
    // 将数组转换为字符串
    const cropPositionStr = convertJSONToFormat(JSON.stringify(CropPositionArray));
    const cropScaleStr = convertJSONToFormat(JSON.stringify(CropScaleArray));
    const cropRotationStr = convertJSONToFormat(JSON.stringify(CropRotationArray));

    // 构建包含所需数据的JSON对象
    const data = {
        id: id,
        CropPosition: cropPositionStr,
        CropScale: cropScaleStr,
        CropRotation: cropRotationStr
    };

    // 发送POST请求
    fetch(ClientServer_URL + '/updataCropPositionAndScale', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Crop矩阵写入成功', data);
            // 在这里可以处理成功响应的逻辑
        })
        .catch(error => {
            console.error('Error updating crop matrix:', error);
            // 在这里可以处理错误响应的逻辑
        });
}

function init(CropPosition, CropScale, CropRotation) {

    // 获取渲染窗口宽高
    const canvasContainer2 = document.getElementById('canvas-container');

    // camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 100);
    camera = new THREE.PerspectiveCamera(45, canvasContainer2.offsetWidth / canvasContainer2.offsetHeight, 0.1, 100);
    camera.position.y = 100;

    // scene

    scene = new THREE.Scene();

    const ambientLight = new THREE.AmbientLight(0xffffff);
    ambientLight.intensity = 0.5; // 将强度设置为2
    // scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0xffffff, 12000);
    camera.add(pointLight);
    scene.add(camera);

    // 加载点云文件
    // 创建PLY加载器
    const loader = new PLYLoader();

    let fileUrl = updata_http + "uploads/" + idKey + "/pcd/point_cloud.ply";
    loader.load(fileUrl, (geometry) => {
        // 创建点云材质
        const material = new THREE.PointsMaterial({
            size: 0.005,
            vertexColors: true
        });

        // 创建点云对象
        const points = new THREE.Points(geometry, material);
        points.scale.setScalar(1);
        // 旋转场景绕 X 轴 -90°
        // points.rotation.x = -Math.PI / 2;

        // geometry赋值给全局变量
        geometry_PLY = geometry;
        geometry_PLY_Reset = geometry;

        // 创建包围盒几何体
        const boundingBoxGeometry = new THREE.BoxGeometry();
        // 创建包围盒材质
        // const boundingBoxMaterial = new THREE.MeshBasicMaterial({ color: 0xff0000, wireframe: true });
        const boundingBoxMaterial = new THREE.MeshBasicMaterial({ color: 0x0000ff, transparent: true, opacity: 0.25 });

        // 创建包围盒网格对象
        boundingBoxMesh = new THREE.Mesh(boundingBoxGeometry, boundingBoxMaterial);

        // 原始的位置和缩放参数
        // const originalPosition = new THREE.Vector3(-3.76224518e-03, -9.04321671e-04, -0.8);
        // const originalScale = new THREE.Vector3(1.82353032, 2.01266909, 1.37428686);
        const originalPosition = CropPosition;
        const originalScale = CropScale;
        const originalRotation = CropRotation;

        // 调用函数来创建立方体
        createCube(originalPosition, originalScale);

        // TransformControl
        createTransformControl();

        // 初始化点云裁剪(取消初始化裁剪)
        // CutBoundboxPly(originalPosition, originalScale);

        // 调整相机位置和缩放以适应包围盒
        const maxDimension = Math.max(originalScale.x, originalScale.y, originalScale.z);
        const distance = maxDimension / Math.sin(Math.PI / 8); // 视角为45度
        camera.position.copy(originalPosition);
        camera.position.z += distance;

        // 设置相机的缩放以确保整个包围盒可见
        const fov = camera.fov * (Math.PI / 180);
        const cameraZ = Math.abs((maxDimension / 2) / Math.tan(fov / 2));
        // 获取浏览器宽高
        const aspect = window.innerWidth / window.innerHeight;

        const fovX = 2 * Math.atan((originalScale.x / 2) / cameraZ);
        const fovY = 2 * Math.atan((originalScale.y / 2) / cameraZ);
        const fovMax = Math.max(fovX, fovY);
        const dist = Math.abs((maxDimension / 2) / Math.sin(fovMax / 2));
        camera.position.z = dist * 1.5;
        // 改变相机轴适应点云坐标
        camera.up.set(0, 0, 1);
        var cameraBoundingSphere = new THREE.Sphere(originalPosition, maxDimension / 2);

        // 将包围盒网格对象添加到场景中
        scene.add(boundingBoxMesh);

        // 添加点云到场景
        scene.add(points);

        scene.background = new THREE.Color(0xf6f4f2); // 白色背景
        // scene.background = new THREE.Color(0x000000); // 黑色背景

        // 设置初始相机位置和目标点
        camera.lookAt(originalPosition);

        // 渲染场景
        renderer.render(scene, camera);

        // 创建控制器
        controls = new OrbitControls(camera, renderer.domElement);
        controls.target.copy(originalPosition);

        // 启用自动旋转
        // controls.autoRotate = true;

        // 设置旋转速度（默认是 2.0，可以根据需要调整）
        controls.autoRotateSpeed = 1.0;

        // 更新控制器
        controls.update();

        // 限制缩放
        controls.maxDistance = cameraBoundingSphere.radius * 10;
        controls.minDistance = cameraBoundingSphere.radius * 0.5;

        // 启用阻尼
        // controls.enableDamping = true;

        // 设置阻尼系数
        // controls.dampingFactor = 0.1;

        // 更新边界框
        updateBoundingBox();

    });

    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(window.devicePixelRatio);
    // 获取渲染窗口宽高
    const canvasContainer = document.getElementById('canvas-container');

    // renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setSize(canvasContainer.offsetWidth, canvasContainer.offsetHeight);
    // document.body.appendChild(renderer.domElement);

    // 将 Canvas 元素添加到 canvas-container 中
    canvasContainer.appendChild(renderer.domElement);

    // 监控窗口缩放
    window.addEventListener('resize', onWindowResize);

    window.addEventListener('mousemove', onMouseMove, false);
    window.addEventListener('mousedown', onMouseDown, false);
    window.addEventListener('mouseup', onMouseUp, false);

}

// 根据入参创建BOX
function createCube(originalPosition, originalScale) {
    for (let i = 0; i < 6; i++) {
        const planeMaterial = new THREE.MeshBasicMaterial({
            color: planeColors[i],
            transparent: true,
            opacity: 0.0,
        });
        const plane = new THREE.Mesh(planeGeometry, planeMaterial);
        planes.push(plane);

        // 根据平面的方向设置法线方向
        let planeNormal;
        switch (i) {
            case 0:
                plane.rotation.x = -Math.PI / 2;
                plane.position.y = originalScale.y / 2;
                planeNormal = new THREE.Vector3(0, 1, 0);
                break;
            case 1:
                plane.rotation.x = Math.PI / 2;
                plane.position.y = -originalScale.y / 2;
                planeNormal = new THREE.Vector3(0, -1, 0);
                break;
            case 2:
                plane.position.z = originalScale.z / 2;
                planeNormal = new THREE.Vector3(0, 0, 1);
                break;
            case 3:
                plane.rotation.y = Math.PI;
                plane.position.z = -originalScale.z / 2;
                planeNormal = new THREE.Vector3(0, 0, -1);
                break;
            case 4:
                plane.rotation.y = -Math.PI / 2;
                plane.position.x = -originalScale.x / 2;
                planeNormal = new THREE.Vector3(-1, 0, 0);
                break;
            case 5:
                plane.rotation.y = Math.PI / 2;
                plane.position.x = originalScale.x / 2;
                planeNormal = new THREE.Vector3(1, 0, 0);
                break;
        }
        plane.userData.normal = planeNormal; // Store the normal as user data

        scene.add(plane);
    }

    // 将整个立方体的位置设置为原始位置
    planes.forEach((plane) => {
        plane.position.add(originalPosition);
    });
    // planes.rotation.x = 0.5;
}

// 点云根据boundbox裁剪函数
function CutBoundboxPly(paramCenter, paramScale) {
    // 保存原始数据
    if (originalPositions.length === 0) {
        originalPositions = geometry_PLY.getAttribute('position').array.slice();
        originalColors = geometry_PLY.getAttribute('color').array.slice();
    }

    // 计算包围盒的最小和最大坐标
    const minX = paramCenter.x - paramScale.x / 2;
    const maxX = paramCenter.x + paramScale.x / 2;
    const minY = paramCenter.y - paramScale.y / 2;
    const maxY = paramCenter.y + paramScale.y / 2;
    const minZ = paramCenter.z - paramScale.z / 2;
    const maxZ = paramCenter.z + paramScale.z / 2;

    // 遍历点云数据,清除包围盒之外的点
    const pointColors = geometry_PLY.getAttribute('color');
    const positions = geometry_PLY.getAttribute('position');
    const positionsArray = positions.array;
    const newPositions = [];
    const newColors = [];

    for (let i = 0; i < positionsArray.length; i += 3) {
        const x = positionsArray[i];
        const y = positionsArray[i + 1];
        const z = positionsArray[i + 2];

        if (x >= minX && x <= maxX && y >= minY && y <= maxY && z >= minZ && z <= maxZ) {
            // 在包围盒内的点，保留它们的位置和颜色
            newPositions.push(x, y, z);
            const color = new THREE.Color().fromBufferAttribute(pointColors, i / 3);
            newColors.push(color.r, color.g, color.b);
        }
    }

    // 更新几何体数据
    geometry_PLY.setAttribute('position', new THREE.Float32BufferAttribute(newPositions, 3));
    geometry_PLY.setAttribute('color', new THREE.Float32BufferAttribute(newColors, 3));

    // 通知Three.js需要更新几何体
    geometry_PLY.attributes.position.needsUpdate = true;
    geometry_PLY.attributes.color.needsUpdate = true;
}

// 点云根据重置点云状态
function ResetPly() {
    if (originalPositions.length != 0) {
        // 更新几何体数据
        geometry_PLY.setAttribute('position', new THREE.Float32BufferAttribute(originalPositions, 3));
        geometry_PLY.setAttribute('color', new THREE.Float32BufferAttribute(originalColors, 3));

        // 通知Three.js需要更新几何体
        geometry_PLY.attributes.position.needsUpdate = true;
        geometry_PLY.attributes.color.needsUpdate = true;
    }
}

// 更新边界框
function updateBoundingBox() {
    // 关闭btnExportMesh按钮
    btnExportMesh.disabled = true;

    if (boundingBox === null) {
        // 如果边界框不存在，创建一个新的边界框对象
        const group = new THREE.Group();
        // 假设planes是有效的Three.js对象的数组
        planes.forEach(plane => {
            if (plane instanceof THREE.Object3D) {
                group.add(plane);
            } else {
                console.error("Invalid object found in planes array:", plane);
            }
        });

        const box = new THREE.Box3().setFromObject(group);

        boundingBox = new THREE.Box3Helper(box, 0xff0000);
        // 获取边界框的中心点
        box.getCenter(boundingBoxcenter);
        // 获取边界框的尺寸
        boundingBox.box.getSize(boundingBoxScale);

        // 设置包围盒位置和缩放以匹配给定的包围盒中心和尺寸
        boundingBoxMesh.position.copy(boundingBoxcenter);
        boundingBoxMesh.scale.copy(boundingBoxScale);

        scene.add(boundingBox);
        scene.add(group);

    } else {
        // 如果边界框已经存在，更新其尺寸和位置
        const group = new THREE.Group();
        // 假设planes是有效的Three.js对象的数组
        planes.forEach(plane => {
            if (plane instanceof THREE.Object3D) {
                group.add(plane);
            } else {
                console.error("Invalid object found in planes array:", plane);
            }
        });

        // 更新边界框的尺寸和位置
        boundingBox.box = new THREE.Box3().setFromObject(group);

        // 获取边界框的中心点
        boundingBox.box.getCenter(boundingBoxcenter);
        // 获取边界框的尺寸
        boundingBox.box.getSize(boundingBoxScale);

        // 设置包围盒位置和缩放以匹配给定的包围盒中心和尺寸
        boundingBoxMesh.position.copy(boundingBoxcenter);
        boundingBoxMesh.scale.copy(boundingBoxScale);

        // 将 CropPosition 的值分配给对应的输入字段
        document.getElementById('positionX').value = boundingBoxcenter.x;
        document.getElementById('positionY').value = boundingBoxcenter.y;
        document.getElementById('positionZ').value = boundingBoxcenter.z;

        // 将 CropScale 的值分配给对应的输入字段
        document.getElementById('scaleX').value = boundingBoxScale.x;
        document.getElementById('scaleY').value = boundingBoxScale.y;
        document.getElementById('scaleZ').value = boundingBoxScale.z;

        // 添加新的 THREE.Group 到场景中
        scene.add(group);
    }
}

// 监听窗口尺寸变化
function onWindowResize() {

    // 获取渲染窗口宽高
    const canvasContainer = document.getElementById('canvas-container');

    // camera.aspect = window.innerWidth / window.innerHeight;
    camera.aspect = canvasContainer.offsetWidth / canvasContainer.offsetHeight;
    camera.updateProjectionMatrix();

    renderer.setSize(window.innerWidth, window.innerHeight);
    // renderer.setSize(canvasContainer.offsetWidth, canvasContainer.offsetHeight);

}

// 动态修改控制器中心点
function updataBoundControlCenter() {
    let planes_YA = planes[0];
    let planes_YB = planes[1];
    let planes_XA = planes[4];
    let planes_XB = planes[5];
    let planes_ZA = planes[2];
    let planes_ZB = planes[3];
    // Z
    planes_ZA.position.x = (planes_XA.position.x + planes_XB.position.x) / 2;
    planes_ZB.position.x = (planes_XA.position.x + planes_XB.position.x) / 2;
    planes_ZA.position.y = (planes_YA.position.y + planes_YB.position.y) / 2;
    planes_ZB.position.y = (planes_YA.position.y + planes_YB.position.y) / 2;

    // X
    planes_XA.position.z = (planes_ZA.position.z + planes_ZB.position.z) / 2;
    planes_XB.position.z = (planes_ZA.position.z + planes_ZB.position.z) / 2;
    planes_XA.position.y = (planes_YA.position.y + planes_YB.position.y) / 2;
    planes_XB.position.y = (planes_YA.position.y + planes_YB.position.y) / 2;

    // Y
    planes_YA.position.z = (planes_ZA.position.z + planes_ZB.position.z) / 2;
    planes_YB.position.z = (planes_ZA.position.z + planes_ZB.position.z) / 2;
    planes_YA.position.x = (planes_XA.position.x + planes_XB.position.x) / 2;
    planes_YB.position.x = (planes_XA.position.x + planes_XB.position.x) / 2;
}

// 在创建平面的地方同时创建对应的 TransformControl
function createTransformControl() {
    planes.forEach((plane, i) => {
        const transformControl = new TransformControls(camera, renderer.domElement);
        transformControl.setTranslationSnap(0.01);
        transformControl.setSize(0.5);
        transformControl.setSpace('local'); //设置为相对坐标系
        transformControl.visible = true; // 确保一直可见
        transformControl.attach(plane); // 附加到当前平面

        // 设置TransformControls的坐标轴可见性
        if (i == 0 || i == 1) {
            transformControl.showX = false;
            transformControl.showY = false;
        } else if (i == 2 || i == 3) {
            transformControl.showX = false;
            transformControl.showY = false;
        } else if (i == 4 || i == 5) {
            transformControl.showX = false;
            transformControl.showY = false;
        }

        scene.add(transformControl);
        transformControls.push(transformControl); // 将 TransformControl 添加到数组中
    });
}

function onMouseMove(event) {
    if (planeBeingDragged || transformControls.some(control => control.dragging)) {
        controls.enabled = false; // 禁用OrbitControls
        updataBoundControlCenter(); // 启用自动居中控制点
        updateBoundingBox();
    } else if (controls) {
        controls.enabled = true; // 启用OrbitControls
    }
}

function onMouseDown(event) {
    event.preventDefault();
    const mousePosition = new THREE.Vector2((event.clientX / window.innerWidth) * 2 - 1, -(event.clientY / window.innerHeight) * 2 + 1);
    const raycaster = new THREE.Raycaster();
    raycaster.setFromCamera(mousePosition, camera);
    const intersects = raycaster.intersectObjects(planes);
    if (intersects.length > 0) {
        controls.enabled = false; // 禁用OrbitControls
        planeBeingDragged = intersects[0].object;
        const intersection = intersects[0].point;
        initialMousePosition.set(intersection.x, intersection.y, intersection.z);
        initialPlanePosition.copy(planeBeingDragged.position);
    }
}

function onMouseUp(event) {
    event.preventDefault();
    planeBeingDragged = null;
}

function animate() {
    requestAnimationFrame(animate);
    // 更新控制器
    if (controls) {
        controls.update();
    }
    renderer.render(scene, camera);
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

// 重置mesh状态
function ResetMesh(ID) {
    // 指定API的URL
    const apiUrl = ClientServer_URL + "/resetExportFormatState";
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
            ResetMeshProgress(ID);

        })
        .catch(error => {
            console.error('发生错误:', error);
        });
}

// 重置Mesh训练进度
function ResetMeshProgress(ID) {
    // 指定API的URL
    const apiUrl = ClientServer_URL + "/updataExportObjProgress";
    // 构造请求对象
    var requestOptions = {
        method: 'POST',  // 或者 'GET'，取决于你的后端路由
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ id: ID, progressVal: 0 })
    };
    // 发送fetch请求
    fetch(apiUrl, requestOptions)
        .then(response => response.json())
        .then(data => {
            console.log('成功收到响应:', data);
            // 在这里处理后端的响应
            ExportTask(ID);

        })
        .catch(error => {
            console.error('发生错误:', error);
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

                // 获取进度元素
                const loadingText = document.getElementById('loadingText');
                const progressBar = document.getElementById('progressBar');

                // 执行关闭Nerf计算进度显示
                const OBJdialog = document.getElementById('OBJprogress');

                // 判断当前任务训练是否完成
                if (finish) {
                    // 停止轮询

                    // 加载等待时显示进度
                    loadingText.textContent = `${'100%'}`;
                    progressBar.style.width = `${'100%'}`;

                    // 隐藏弹出面板
                    OBJdialog.style.display = 'none';

                } else {
                    // 隐藏弹出面板
                    OBJdialog.style.display = 'block';

                    loadingText.textContent = `${progress + '%'}`;
                    progressBar.style.width = `${progress + '%'}`;
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
                // 获取进度元素
                const loadingText = document.getElementById('loadingText');
                const progressBar = document.getElementById('progressBar');

                // 计算进度显示
                const OBJdialog = document.getElementById('OBJprogress');

                // 判断当前任务如果未完成且未开始训练
                if (!finish && progress == 0) {

                    // 启动btnExportMesh按钮
                    btnExportMesh.disabled = false;
                    return true;

                    // 判断如果任务完成了且进度为100
                } else if (finish && progress == 100) {

                    // 启动btnExportMesh按钮
                    btnExportMesh.disabled = false;
                    return false;

                    // 判断当前任务完成了或已经开始训练了
                } else if (finish || progress != 0) {

                    // 进行轮询检查
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

document.addEventListener('DOMContentLoaded', function () {
    // 页面加载完毕后执行的代码
    // 渲染图标
    feather.replace();

    // 通过idKey请求矩阵数据
    fetchCropData(idKey)
        .then(data => {
            if (data) {
                console.log('CropPosition:', data.CropPosition);
                console.log('CropScale:', data.CropScale);
                console.log('CropRotation:', data.CropRotation);

                // 将 CropPosition 的值分配给对应的输入字段
                document.getElementById('positionX').value = data.CropPosition.x;
                document.getElementById('positionY').value = data.CropPosition.y;
                document.getElementById('positionZ').value = data.CropPosition.z;

                // 将 CropScale 的值分配给对应的输入字段
                document.getElementById('scaleX').value = data.CropScale.x;
                document.getElementById('scaleY').value = data.CropScale.y;
                document.getElementById('scaleZ').value = data.CropScale.z;

                // 将 CropRotation 的值分配给对应的输入字段
                document.getElementById('rotationX').value = data.CropRotation.x;
                document.getElementById('rotationY').value = data.CropRotation.y;
                document.getElementById('rotationZ').value = data.CropRotation.z;

                // 初始化场景
                init(data.CropPosition, data.CropScale, data.CropRotation);
                // 循环帧
                animate();
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });

    // 获取ID为Btn_Apply的按钮元素
    var btnApply = document.getElementById('Btn_Apply');
    btnExportMesh = document.getElementById('Btn_ExportMesh');

    // 给按钮添加点击事件监听器
    btnApply.addEventListener('click', function () {
        // 点击Apply后应用当前裁剪范围
        CutBoundboxPly(boundingBoxcenter, boundingBoxScale);
        // 更新矩阵到数据库
        updateCropPositionAndScale(boundingBoxcenter, boundingBoxScale, boundingBoxRotation, idKey);
        // 启动btnExportMesh按钮
        btnExportMesh.disabled = false;
    });

    // 获取ID为Btn_Reset的按钮元素
    var btnReset = document.getElementById('Btn_Reset');

    // 给按钮添加点击事件监听器
    btnReset.addEventListener('click', function () {
        ResetPly();
        // 关闭btnExportMesh按钮
        btnExportMesh.disabled = true;
    });

    // 给按钮添加点击事件监听器
    btnExportMesh.addEventListener('click', function () {
        console.log("export");
        // 关闭btnExportMesh按钮
        btnExportMesh.disabled = true;
        // 请求构建Mesh
        // ExportTask(idKey);
        // 先重置在构建
        ResetMesh(idKey)

    });

    // 初始查询OBJ训练状态
    Get_SQLData_OBJ_ByID(idKey);


});