<template>
  <div id="app">
    <el-container>
      <el-aside :width="isCollapse ? '72px' : '232px'">
        <div class="sidebar">
          <div class="logo">
            <div class="logo-mark">TP</div>
            <div v-show="!isCollapse" class="logo-copy">
              <h2>Turbo Publisher</h2>
              <span>视频分发工作台</span>
            </div>
          </div>
          <el-menu
            :router="true"
            :default-active="activeMenu"
            :collapse="isCollapse"
            class="sidebar-menu"
          >
            <el-menu-item index="/">
              <el-icon><Upload /></el-icon>
              <span>发布工作台</span>
            </el-menu-item>
            <el-menu-item index="/dashboard">
              <el-icon><HomeFilled /></el-icon>
              <span>数据概览</span>
            </el-menu-item>
            <el-menu-item index="/account-management">
              <el-icon><User /></el-icon>
              <span>账号管理</span>
            </el-menu-item>
            <el-menu-item index="/material-management">
              <el-icon><Picture /></el-icon>
              <span>素材管理</span>
            </el-menu-item>
            <el-menu-item index="/about">
              <el-icon><DataAnalysis /></el-icon>
              <span>关于</span>
            </el-menu-item>
          </el-menu>
        </div>
      </el-aside>
      <el-container>
        <el-header>
          <div class="header-content">
            <div class="header-left">
              <el-icon class="toggle-sidebar" @click="toggleSidebar"><Fold /></el-icon>
              <div class="route-title">
                <strong>{{ pageTitle }}</strong>
                <span>管理账号、素材和发布任务</span>
              </div>
            </div>
            <div class="header-right">
              <span class="runtime-dot"></span>
              <span>本地自动化引擎</span>
            </div>
          </div>
        </el-header>
        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  HomeFilled, User, DataAnalysis,
  Fold, Picture, Upload
} from '@element-plus/icons-vue'

const route = useRoute()

// 当前激活的菜单项
const activeMenu = computed(() => {
  return route.path
})

const pageTitle = computed(() => {
  const titleMap = {
    '/': '发布工作台',
    '/dashboard': '数据概览',
    '/account-management': '账号管理',
    '/material-management': '素材管理',
    '/about': '关于'
  }
  return titleMap[route.path] || '发布工作台'
})

// 侧边栏折叠状态
const isCollapse = ref(false)

// 切换侧边栏折叠状态
const toggleSidebar = () => {
  isCollapse.value = !isCollapse.value
}
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

#app {
  min-height: 100vh;
}

.el-container {
  height: 100vh;
}

.el-aside {
  background: oklch(96.5% 0.006 255);
  color: oklch(29% 0.018 255);
  height: 100vh;
  overflow: hidden;
  transition: width 0.22s ease;
  border-right: 1px solid oklch(89% 0.012 255);

  .sidebar {
    display: flex;
    flex-direction: column;
    height: 100%;

    .logo {
      height: 72px;
      padding: 0 14px;
      display: flex;
      align-items: center;
      gap: 11px;
      overflow: hidden;

      .logo-mark {
        width: 38px;
        height: 38px;
        display: grid;
        place-items: center;
        flex: 0 0 38px;
        border-radius: 8px;
        background: oklch(54% 0.14 238);
        color: oklch(98% 0.005 255);
        font-weight: 800;
        font-size: 13px;
      }

      .logo-copy {
        min-width: 0;

        h2 {
          color: oklch(25% 0.02 255);
          font-size: 15px;
          font-weight: 760;
          white-space: nowrap;
          margin: 0;
          letter-spacing: 0;
        }

        span {
          display: block;
          margin-top: 3px;
          color: oklch(54% 0.025 255);
          font-size: 12px;
          white-space: nowrap;
        }
      }
    }

    .sidebar-menu {
      border-right: none;
      flex: 1;
      padding: 8px;
      background: transparent;

      .el-menu-item {
        display: flex;
        align-items: center;
        height: 42px;
        margin: 4px 0;
        border-radius: 8px;
        color: oklch(43% 0.022 255);

        .el-icon {
          margin-right: 10px;
          font-size: 18px;
        }

        &:hover {
          background: oklch(92.5% 0.018 238);
          color: oklch(38% 0.1 238);
        }

        &.is-active {
          background: oklch(90.5% 0.04 238);
          color: oklch(40% 0.13 238);
          font-weight: 680;
        }
      }
    }
  }
}

.el-header {
  background: oklch(98.5% 0.004 255);
  border-bottom: 1px solid oklch(91% 0.01 255);
  padding: 0;
  height: 64px;

  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    height: 100%;
    padding: 0 16px;

    .header-left {
      display: flex;
      align-items: center;
      gap: 14px;

      .toggle-sidebar {
        font-size: 20px;
        cursor: pointer;
        color: oklch(45% 0.025 255);

        &:hover {
          color: oklch(45% 0.13 238);
        }
      }

      .route-title {
        display: flex;
        flex-direction: column;

        strong {
          font-size: 15px;
          color: oklch(27% 0.018 255);
        }

        span {
          margin-top: 3px;
          color: oklch(55% 0.02 255);
          font-size: 12px;
        }
      }
    }

    .header-right {
      display: flex;
      align-items: center;
      gap: 8px;
      color: oklch(48% 0.025 255);
      font-size: 13px;

      .runtime-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: oklch(62% 0.16 150);
      }
    }
  }
}

.el-main {
  background: oklch(94.5% 0.007 255);
  padding: 24px;
  overflow-y: auto;
}

@media (max-width: 760px) {
  .el-aside {
    display: none;
  }

  .el-main {
    padding: 16px;
  }

  .route-title span,
  .header-right {
    display: none !important;
  }
}
</style>
