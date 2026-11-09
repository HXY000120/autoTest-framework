// 今日资讯平台测试项目 - Jenkins Pipeline（Windows agent / 自建 Runner）
// 依赖：Jenkins Allure Plugin；Web 阶段需本机浏览器，App 阶段需 adb 设备 + Appium 服务
pipeline {
    agent any

    parameters {
        booleanParam(name: 'RUN_REAL', defaultValue: false,
                     description: '真实环境联调（打开后才发真实请求用例）')
        booleanParam(name: 'RUN_WEB', defaultValue: false,
                     description: '执行 Web UI 用例（需本机浏览器）')
        booleanParam(name: 'RUN_APP', defaultValue: false,
                     description: '执行 App UI 用例（需真机/模拟器 + Appium）')
    }

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    stages {
        stage('准备环境') {
            steps {
                bat 'python -m venv .venv'
                bat '.venv\\Scripts\\python.exe -m pip install --upgrade pip'
                bat '.venv\\Scripts\\python.exe -m pip install -r requirements.txt'
                bat '.venv\\Scripts\\python.exe -m common.report.report clean'
            }
        }

        stage('接口自动化') {
            steps {
                script {
                    // 密码按日期轮换：前缀存 Jenkins 全局环境变量，这里拼当天日期，
                    // 仓库内不出现任何真实密码。
                    def today = new Date().format('yyyyMMdd')
                    withEnv([
                        "RUN_REAL=${params.RUN_REAL ? '1' : '0'}",
                        "MP_PASSWORD=${env.MP_PWD_PREFIX ? env.MP_PWD_PREFIX + today : ''}",
                        "MIS_PASSWORD=${env.MIS_PWD_PREFIX ? env.MIS_PWD_PREFIX + today : ''}",
                    ]) {
                        // 接口阶段不收集 UI 目录：避免 CI 只装基础依赖时因 selenium 缺失中断收集
                        bat '.venv\\Scripts\\python.exe -m pytest -m api --ignore=script/app/ui --ignore=script/mp/ui --ignore=script/mis/ui --alluredir=reports/raw'
                    }
                }
            }
        }

        stage('Web 自动化') {
            when { expression { params.RUN_WEB } }
            steps {
                bat '.venv\\Scripts\\python.exe -m pip install -r requirements-web.txt'
                script {
                    def today = new Date().format('yyyyMMdd')
                    withEnv([
                        "RUN_REAL=${params.RUN_REAL ? '1' : '0'}",
                        "MP_PASSWORD=${env.MP_PWD_PREFIX ? env.MP_PWD_PREFIX + today : ''}",
                        "MIS_PASSWORD=${env.MIS_PWD_PREFIX ? env.MIS_PWD_PREFIX + today : ''}",
                    ]) {
                        bat '.venv\\Scripts\\python.exe -m pytest -m web --alluredir=reports/raw'
                    }
                }
            }
        }

        stage('App 自动化（组件单测）') {
            when { expression { params.RUN_APP } }
            steps {
                bat '.venv\\Scripts\\python.exe -m pytest -m app --alluredir=reports/raw'
            }
        }
    }

    post {
        always {
            // Allure 命令行由插件联网下载，离线/受限网络下会失败；
            // 报告生成失败只降级为 UNSTABLE，不让整条流水线变红。
            catchError(buildResult: 'SUCCESS', stageResult: 'UNSTABLE') {
                allure includeProperties: false, results: [[path: 'reports/raw']]
            }
            archiveArtifacts artifacts: 'reports/**, logs/**', allowEmptyArchive: true
        }
    }
}
