// Call this from worker thread.
void run_in_main_thread(std::function<void>&& func) {
    std::deque<std::function<void>> queue;
    std::mutex mutex;

    auto main_thread_timer_proc = [](HWND hwnd, UINT msg, UINT_PTR wparam, DWORD lparam) {
        std::lock_guard<std::mutex> guard(g_pages_mutex);
        while (!queue.empty()) {
            std::function<void()> func = std::move(queue.front());
            queue.pop();
            func();  // call in main thread.
        }
        KillTimer(timer);
    };

    std::lock_guard<std::mutex> guard(g_pages_mutex);
    queue.push(std::move(func));
    auto timer = SetTimer(NULL, 0, 0, main_thread_timer_proc);
}
