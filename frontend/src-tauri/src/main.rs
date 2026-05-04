// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

/// 桌面端可执行文件入口，委托库 crate 完成 Tauri 初始化和运行。
/// 该函数不处理业务错误，启动失败会由 Tauri 运行时或库层日志暴露。
fn main() {
    plotpilot_lib::run()
}
