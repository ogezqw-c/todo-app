/**
 * TaskFlow — 前端交互脚本
 */

document.addEventListener('DOMContentLoaded', function () {

    // ---- 删除确认 ----
    document.querySelectorAll('.delete-form').forEach(function (form) {
        form.addEventListener('submit', function (e) {
            if (!confirm('确定要删除吗？此操作不可撤销。')) {
                e.preventDefault();
            }
        });
    });

    // ---- Flash 消息 4 秒后自动消失 ----
    document.querySelectorAll('.alert-dismissible').forEach(function (alert) {
        setTimeout(function () {
            var bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 4000);
    });

    // ---- 任务完成状态行内切换（乐观更新） ----
    document.querySelectorAll('.toggle-form').forEach(function (form) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            var btn = form.querySelector('.toggle-btn');
            if (!btn) return;

            var icon = btn.querySelector('i');
            var wasCompleted = icon.classList.contains('bi-check-circle-fill');

            // 乐观更新 UI（先翻转再请求）
            if (wasCompleted) {
                icon.classList.remove('bi-check-circle-fill');
                icon.classList.add('bi-circle');
                btn.style.color = 'var(--text-muted)';
            } else {
                icon.classList.remove('bi-circle');
                icon.classList.add('bi-check-circle-fill');
                btn.style.color = 'var(--success)';
            }
            // 按钮弹跳反馈
            btn.style.transform = 'scale(1.3)';
            setTimeout(function () { btn.style.transform = 'scale(1)'; }, 200);

            fetch(form.action, { method: 'POST' })
                .then(function (r) {
                    if (!r.ok) throw new Error('Network error');
                    // 请求成功后刷新页面以同步后端状态
                    setTimeout(function () { window.location.reload(); }, 300);
                })
                .catch(function () {
                    // 回滚 UI
                    if (wasCompleted) {
                        icon.classList.remove('bi-circle');
                        icon.classList.add('bi-check-circle-fill');
                        btn.style.color = 'var(--success)';
                    } else {
                        icon.classList.remove('bi-check-circle-fill');
                        icon.classList.add('bi-circle');
                        btn.style.color = 'var(--text-muted)';
                    }
                    btn.style.transform = 'scale(1)';
                    alert('操作失败，请重试。');
                });
        });
    });

    // ---- 入场动画：给带 .animate-in 的元素逐条触发 ----
    document.querySelectorAll('.animate-in').forEach(function (el, i) {
        el.style.animationDelay = (i * 0.06) + 's';
    });

});
