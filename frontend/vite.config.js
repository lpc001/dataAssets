import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
// 解析 @ 别名为 src 目录（tsconfig 已配置 paths，这里补上 Vite 侧解析）。
// 项目未安装 @types/node，故用 URL 构造避免引入 node:path / node:url 类型依赖。
var srcAlias = decodeURIComponent(new URL('./src', import.meta.url).pathname).replace(/^\/([A-Za-z]:)/, '$1');
export default defineConfig({
    plugins: [vue()],
    resolve: {
        alias: {
            '@': srcAlias,
        },
    },
    server: {
        port: 5173,
        proxy: {
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true,
            },
        },
    },
});
