<template>
  <div class="publisher-workspace">
    <section class="workspace-header">
      <div>
        <p class="eyebrow">Video Distribution Console</p>
        <h1>一条视频，多平台发布</h1>
        <p class="subtitle">上传素材，选择账号，统一填写标题、简介、话题，然后分发到抖音、快手、小红书、视频号和 Bilibili。</p>
      </div>
      <div class="header-actions">
        <el-button :icon="Refresh" @click="loadInitialData" :loading="loading">刷新</el-button>
        <el-button type="primary" :icon="UploadFilled" @click="submitPublish" :loading="publishing">
          提交到 {{ enabledTargetCount || 0 }} 个平台
        </el-button>
      </div>
    </section>

    <section class="status-strip">
      <div class="status-item">
        <span class="label">平台</span>
        <strong>{{ platforms.length }}</strong>
      </div>
      <div class="status-item">
        <span class="label">账号文件</span>
        <strong>{{ accounts.length }}</strong>
      </div>
      <div class="status-item">
        <span class="label">视频素材</span>
        <strong>{{ videoMaterials.length }}</strong>
      </div>
      <div class="status-item">
        <span class="label">最近任务</span>
        <strong>{{ jobs.length }}</strong>
      </div>
    </section>

    <section class="flow-strip">
      <div class="flow-step done">
        <span>1</span>
        <strong>素材</strong>
      </div>
      <div class="flow-step" :class="{ done: form.title }">
        <span>2</span>
        <strong>文案</strong>
      </div>
      <div class="flow-step" :class="{ done: enabledTargetCount > 0 }">
        <span>3</span>
        <strong>平台</strong>
      </div>
      <div class="flow-step" :class="{ done: activeJob }">
        <span>4</span>
        <strong>任务</strong>
      </div>
    </section>

    <main class="workspace-grid">
      <section class="panel compose-panel">
        <div class="panel-heading">
          <div>
            <h2>发布内容</h2>
            <p>所有平台共用的基础素材和文案。</p>
          </div>
        </div>

        <el-form label-position="top" class="compose-form">
          <el-form-item label="视频素材">
            <div class="upload-row">
              <el-upload
                class="compact-upload"
                :show-file-list="false"
                :http-request="(options) => uploadAsset(options, 'video')"
                accept="video/*"
              >
                <el-button :icon="Upload">上传视频</el-button>
              </el-upload>
              <el-select v-model="form.videoPath" placeholder="选择已上传视频" filterable>
                <el-option
                  v-for="material in videoMaterials"
                  :key="material.path"
                  :label="material.original_name"
                  :value="material.path"
                />
              </el-select>
            </div>
            <p v-if="selectedVideo" class="field-hint">已选：{{ selectedVideo.original_name }}，{{ selectedVideo.size_mb }} MB</p>
          </el-form-item>

          <el-form-item label="封面">
            <div class="upload-row">
              <el-upload
                class="compact-upload"
                :show-file-list="false"
                :http-request="(options) => uploadAsset(options, 'thumbnail')"
                accept="image/*"
              >
                <el-button :icon="Picture">上传封面</el-button>
              </el-upload>
              <el-select v-model="form.thumbnailPath" placeholder="可选" clearable filterable>
                <el-option
                  v-for="material in thumbnailMaterials"
                  :key="material.path"
                  :label="material.original_name"
                  :value="material.path"
                />
              </el-select>
            </div>
            <p v-if="selectedThumbnail" class="field-hint">已选封面：{{ selectedThumbnail.original_name }}</p>
          </el-form-item>

          <el-form-item label="标题">
            <el-input v-model="form.title" maxlength="80" show-word-limit placeholder="例如：AI 自动化工作流实测" />
          </el-form-item>

          <el-form-item label="简介">
            <el-input
              v-model="form.description"
              type="textarea"
              :rows="4"
              maxlength="500"
              show-word-limit
              placeholder="填写视频简介，平台会尽量复用这段内容。"
            />
          </el-form-item>

          <el-form-item label="话题">
            <el-input v-model="form.rawTags" placeholder="用逗号分隔，例如 AI工具,自动化,出海" />
          </el-form-item>

          <div class="split-fields">
            <el-form-item label="发布时间">
              <el-radio-group v-model="form.publishMode">
                <el-radio-button label="now">立即</el-radio-button>
                <el-radio-button label="schedule">定时</el-radio-button>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="定时时间" v-if="form.publishMode === 'schedule'">
              <el-date-picker
                v-model="form.schedule"
                type="datetime"
                format="YYYY-MM-DD HH:mm"
                value-format="YYYY-MM-DD HH:mm"
                placeholder="至少晚于当前 2 小时"
              />
            </el-form-item>
          </div>
        </el-form>
      </section>

      <section class="panel platform-panel">
        <div class="panel-heading">
          <div>
            <h2>发布目标</h2>
            <p>给每个平台选择一个账号。视频号当前是 beta；Bilibili 登录仍建议用 CLI。</p>
          </div>
          <el-button :icon="User" @click="loginDialogVisible = true">登录账号</el-button>
        </div>

        <div class="platform-list">
          <article
            v-for="platform in platforms"
            :key="platform.key"
            class="platform-row"
            :class="{ selected: selectedTargets[platform.key]?.enabled }"
          >
            <div class="platform-main">
              <el-checkbox v-model="selectedTargets[platform.key].enabled" />
              <div>
                <div class="platform-title">
                  <span>{{ platform.label }}</span>
                  <el-tag v-if="platform.status === 'beta'" size="small" type="warning" effect="plain">Beta</el-tag>
                </div>
                <p>{{ platform.schedule ? '支持定时发布' : '仅立即发布' }} · {{ platform.note ? '支持图文' : '视频优先' }}</p>
              </div>
            </div>
            <el-select
              v-model="selectedTargets[platform.key].accountName"
              :disabled="!selectedTargets[platform.key].enabled"
              placeholder="选择账号"
              filterable
            >
              <el-option
                v-for="account in accountsByPlatform(platform.key)"
                :key="account.account_file"
                :label="account.account_name"
                :value="account.account_name"
              />
            </el-select>
            <p
              v-if="selectedTargets[platform.key].enabled && accountsByPlatform(platform.key).length === 0"
              class="missing-account"
            >
              还没有 {{ platform.label }} 账号文件
            </p>
            <div v-if="platform.key === 'tencent' && selectedTargets.tencent.enabled" class="target-options">
              <el-input v-model="selectedTargets.tencent.shortTitle" placeholder="视频号短标题，可选" />
              <el-checkbox v-model="selectedTargets.tencent.draft">保存草稿</el-checkbox>
            </div>
            <div v-if="platform.key === 'bilibili' && selectedTargets.bilibili.enabled" class="target-options">
              <el-input v-model="selectedTargets.bilibili.tid" placeholder="Bilibili 分区 tid，例如 249" />
            </div>
          </article>
        </div>
      </section>

      <section class="panel task-panel">
        <div class="panel-heading">
          <div>
            <h2>任务状态</h2>
            <p>发布任务会顺序执行，避免多个平台同时抢浏览器资源。</p>
          </div>
        </div>

        <div v-if="activeJob" class="active-job">
          <div class="job-summary">
            <el-tag :type="jobTagType(activeJob.status)" effect="plain">{{ statusText(activeJob.status) }}</el-tag>
            <span>{{ activeJob.message }}</span>
          </div>
          <el-timeline>
            <el-timeline-item
              v-for="(step, index) in activeJob.steps"
              :key="`${step.platform}-${index}`"
              :type="timelineType(step.status)"
              :timestamp="formatTime(step.time)"
            >
              {{ step.message }}
            </el-timeline-item>
          </el-timeline>
        </div>

        <div v-else class="task-empty">
          <div class="task-empty-icon">
            <el-icon><UploadFilled /></el-icon>
          </div>
          <strong>还没有发布任务</strong>
          <span>提交后会显示每个平台的运行状态。</span>
        </div>

        <div v-if="jobs.length" class="recent-jobs">
          <h3>最近任务</h3>
          <button
            v-for="job in jobs.slice(0, 5)"
            :key="job.id"
            class="job-row"
            type="button"
            @click="activeJob = job"
          >
            <span>{{ job.message }}</span>
            <el-tag size="small" :type="jobTagType(job.status)" effect="plain">{{ statusText(job.status) }}</el-tag>
          </button>
        </div>
      </section>
    </main>

    <el-dialog v-model="loginDialogVisible" title="登录账号" width="520px">
      <el-form label-position="top">
        <el-form-item label="平台">
          <el-select v-model="loginForm.platform" class="w-full">
            <el-option
              v-for="platform in loginablePlatforms"
              :key="platform.key"
              :label="platform.label"
              :value="platform.key"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="账号名称">
          <el-input v-model="loginForm.accountName" placeholder="例如 creator、brand01" />
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="loginForm.headed">显示浏览器窗口</el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="loginDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="loggingIn" @click="startLogin">开始登录</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Picture,
  Refresh,
  Upload,
  UploadFilled,
  User
} from '@element-plus/icons-vue'
import { platformApi } from '@/api/platform'

const loading = ref(false)
const publishing = ref(false)
const loggingIn = ref(false)
const loginDialogVisible = ref(false)
const platforms = ref([])
const accounts = ref([])
const materials = ref([])
const jobs = ref([])
const activeJob = ref(null)
let pollingTimer = null

const form = reactive({
  videoPath: '',
  thumbnailPath: '',
  title: '',
  description: '',
  rawTags: '',
  publishMode: 'now',
  schedule: ''
})

const loginForm = reactive({
  platform: 'douyin',
  accountName: 'creator',
  headed: true
})

const selectedTargets = reactive({
  douyin: { enabled: true, accountName: '' },
  kuaishou: { enabled: false, accountName: '' },
  xiaohongshu: { enabled: false, accountName: '' },
  tencent: { enabled: false, accountName: '', shortTitle: '', draft: false },
  bilibili: { enabled: false, accountName: '', tid: '' }
})

const videoMaterials = computed(() => materials.value.filter((item) => item.kind === 'video'))
const thumbnailMaterials = computed(() => materials.value.filter((item) => item.kind === 'thumbnail'))
const loginablePlatforms = computed(() => platforms.value.filter((platform) => platform.web_login))
const selectedVideo = computed(() => videoMaterials.value.find((item) => item.path === form.videoPath))
const selectedThumbnail = computed(() => thumbnailMaterials.value.find((item) => item.path === form.thumbnailPath))
const enabledTargetCount = computed(() => Object.values(selectedTargets).filter((target) => target.enabled).length)

const accountsByPlatform = (platformKey) => {
  return accounts.value.filter((account) => account.platform === platformKey)
}

const normalizePayloadTargets = () => {
  return Object.entries(selectedTargets)
    .filter(([, target]) => target.enabled)
    .map(([platform, target]) => {
      const settings = {}
      if (platform === 'tencent') {
        settings.short_title = target.shortTitle
        settings.draft = target.draft
      }
      if (platform === 'bilibili') {
        settings.tid = target.tid
      }
      return {
        platform,
        account_name: target.accountName,
        settings
      }
    })
}

const loadInitialData = async () => {
  loading.value = true
  try {
    const [platformRes, accountRes, materialRes, jobRes] = await Promise.all([
      platformApi.getPlatforms(),
      platformApi.getAccounts(),
      platformApi.getMaterials(),
      platformApi.getJobs()
    ])
    platforms.value = platformRes.data || []
    accounts.value = accountRes.data || []
    materials.value = materialRes.data || []
    jobs.value = jobRes.data || []
  } finally {
    loading.value = false
  }
}

const uploadAsset = async (options, kind) => {
  const formData = new FormData()
  formData.append('file', options.file)
  formData.append('kind', kind)
  const response = await platformApi.uploadMaterial(formData)
  materials.value.unshift(response.data)
  if (kind === 'video') {
    form.videoPath = response.data.path
  } else {
    form.thumbnailPath = response.data.path
  }
  options.onSuccess(response.data)
}

const validatePublish = () => {
  if (!form.videoPath) return '请选择或上传视频'
  if (!form.title.trim()) return '标题不能为空'
  if (form.publishMode === 'schedule' && !form.schedule) return '请选择定时时间'
  const targets = normalizePayloadTargets()
  if (!targets.length) return '至少选择一个发布平台'
  const missingAccount = targets.find((target) => !target.account_name)
  if (missingAccount) return `${platformLabel(missingAccount.platform)} 缺少账号`
  const bili = targets.find((target) => target.platform === 'bilibili')
  if (bili && !bili.settings.tid) return 'Bilibili 需要填写分区 tid'
  return ''
}

const submitPublish = async () => {
  const error = validatePublish()
  if (error) {
    ElMessage.warning(error)
    return
  }

  publishing.value = true
  try {
    const response = await platformApi.publish({
      video_path: form.videoPath,
      thumbnail_path: form.thumbnailPath,
      title: form.title.trim(),
      description: form.description,
      raw_tags: form.rawTags,
      schedule: form.publishMode === 'schedule' ? form.schedule : '',
      targets: normalizePayloadTargets(),
      headless: true,
      debug: true
    })
    activeJob.value = response.data
    ElMessage.success('发布任务已提交')
    startPolling(response.data.id)
  } finally {
    publishing.value = false
  }
}

const startLogin = async () => {
  if (!loginForm.accountName.trim()) {
    ElMessage.warning('账号名称不能为空')
    return
  }
  loggingIn.value = true
  try {
    const response = await platformApi.loginAccount({
      platform: loginForm.platform,
      account_name: loginForm.accountName.trim(),
      headless: !loginForm.headed
    })
    activeJob.value = response.data
    loginDialogVisible.value = false
    ElMessage.success('登录任务已启动，请按浏览器或终端提示扫码')
    startPolling(response.data.id, true)
  } finally {
    loggingIn.value = false
  }
}

const startPolling = (jobId, refreshAccounts = false) => {
  if (pollingTimer) window.clearInterval(pollingTimer)
  pollingTimer = window.setInterval(async () => {
    const response = await platformApi.getJob(jobId)
    activeJob.value = response.data
    if (['success', 'failed', 'partial'].includes(response.data.status)) {
      window.clearInterval(pollingTimer)
      pollingTimer = null
      const jobsResponse = await platformApi.getJobs()
      jobs.value = jobsResponse.data || []
      if (refreshAccounts) {
        const accountResponse = await platformApi.getAccounts()
        accounts.value = accountResponse.data || []
      }
    }
  }, 2000)
}

const platformLabel = (platformKey) => {
  return platforms.value.find((platform) => platform.key === platformKey)?.label || platformKey
}

const statusText = (status) => {
  return {
    queued: '排队中',
    running: '运行中',
    success: '成功',
    failed: '失败',
    partial: '部分成功'
  }[status] || status
}

const jobTagType = (status) => {
  return {
    success: 'success',
    failed: 'danger',
    partial: 'warning',
    running: 'primary',
    queued: 'info'
  }[status] || 'info'
}

const timelineType = (status) => {
  return {
    success: 'success',
    failed: 'danger',
    running: 'primary'
  }[status] || 'info'
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  return new Date(timestamp * 1000).toLocaleTimeString()
}

onMounted(loadInitialData)
</script>

<style lang="scss" scoped>
.publisher-workspace {
  color: oklch(27% 0.02 255);
}

.workspace-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 18px;
  padding: 6px 2px 0;

  h1 {
    margin: 4px 0 8px;
    font-size: 30px;
    line-height: 1.2;
    font-weight: 760;
    letter-spacing: 0;
  }
}

.eyebrow {
  margin: 0;
  font-size: 12px;
  font-weight: 700;
  color: oklch(50% 0.11 238);
  text-transform: uppercase;
}

.subtitle {
  max-width: 760px;
  margin: 0;
  color: oklch(46% 0.025 255);
  line-height: 1.6;
}

.header-actions {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}

:deep(.el-button) {
  border-radius: 7px;
  font-weight: 650;
}

:deep(.el-button--primary) {
  background-color: oklch(52% 0.14 238);
  border-color: oklch(52% 0.14 238);

  &:hover,
  &:focus {
    background-color: oklch(47% 0.15 238);
    border-color: oklch(47% 0.15 238);
  }
}

.status-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1px;
  overflow: hidden;
  margin-bottom: 20px;
  border: 1px solid oklch(89% 0.012 255);
  border-radius: 8px;
  background: oklch(89% 0.012 255);
}

.status-item {
  padding: 14px 16px;
  background: oklch(98% 0.004 255);

  .label {
    display: block;
    color: oklch(52% 0.025 255);
    font-size: 12px;
    margin-bottom: 5px;
  }

  strong {
    font-size: 22px;
  }
}

.flow-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 18px;
}

.flow-step {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 46px;
  padding: 10px 12px;
  border: 1px solid oklch(88% 0.012 255);
  border-radius: 8px;
  background: oklch(97.5% 0.004 255);
  color: oklch(52% 0.025 255);

  span {
    width: 24px;
    height: 24px;
    display: grid;
    place-items: center;
    border-radius: 50%;
    background: oklch(91% 0.012 255);
    font-size: 12px;
    font-weight: 760;
  }

  strong {
    font-size: 13px;
  }

  &.done {
    border-color: oklch(78% 0.08 238);
    color: oklch(36% 0.1 238);

    span {
      background: oklch(52% 0.14 238);
      color: oklch(98% 0.005 255);
    }
  }
}

.workspace-grid {
  display: grid;
  grid-template-columns: minmax(360px, 1.05fr) minmax(360px, 1fr);
  gap: 18px;
  align-items: start;
}

.panel {
  border: 1px solid oklch(88.5% 0.012 255);
  border-radius: 8px;
  background: oklch(98.7% 0.004 255);
  padding: 22px;
  box-shadow: 0 14px 38px oklch(34% 0.03 255 / 0.06);
}

.compose-panel {
  grid-row: span 2;
}

.task-panel {
  grid-column: 2;
}

.panel-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;

  h2 {
    margin: 0 0 4px;
    font-size: 17px;
  }

  p {
    margin: 0;
    color: oklch(52% 0.025 255);
    font-size: 13px;
  }
}

.upload-row {
  display: grid;
  grid-template-columns: 124px 1fr;
  gap: 10px;
  width: 100%;
}

.field-hint {
  margin: 8px 0 0;
  color: oklch(49% 0.03 255);
  font-size: 12px;
}

.split-fields {
  display: grid;
  grid-template-columns: minmax(160px, 220px) 1fr;
  gap: 12px;
}

.platform-list {
  display: grid;
  gap: 10px;
}

.platform-row {
  display: grid;
  grid-template-columns: 1fr minmax(170px, 220px);
  gap: 12px;
  align-items: center;
  padding: 14px;
  border: 1px solid oklch(90% 0.012 255);
  border-radius: 8px;
  background: oklch(99% 0.003 255);

  &.selected {
    border-color: oklch(72% 0.11 238);
    background: oklch(96.5% 0.018 238);
  }
}

.platform-main {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.platform-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 680;
}

.platform-main p {
  margin: 4px 0 0;
  color: oklch(52% 0.025 255);
  font-size: 12px;
}

.missing-account {
  grid-column: 1 / -1;
  margin: -2px 0 0 34px;
  color: oklch(52% 0.14 35);
  font-size: 12px;
}

.target-options {
  grid-column: 1 / -1;
  display: flex;
  gap: 10px;
  align-items: center;
  padding-left: 34px;
}

.active-job {
  min-height: 120px;
}

.job-summary {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.task-empty {
  min-height: 185px;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 8px;
  color: oklch(50% 0.025 255);
  text-align: center;
  border: 1px dashed oklch(84% 0.014 255);
  border-radius: 8px;
  background: oklch(97% 0.004 255);

  strong {
    color: oklch(31% 0.02 255);
  }

  span {
    font-size: 13px;
  }
}

.task-empty-icon {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: oklch(92% 0.025 238);
  color: oklch(43% 0.13 238);
  font-size: 20px;
}

.recent-jobs {
  margin-top: 18px;

  h3 {
    margin: 0 0 8px;
    font-size: 14px;
  }
}

.job-row {
  width: 100%;
  min-height: 38px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 8px 0;
  border: 0;
  border-top: 1px solid oklch(91% 0.01 255);
  background: transparent;
  color: inherit;
  text-align: left;
  cursor: pointer;
  transition: color 0.18s ease, background-color 0.18s ease;

  &:hover {
    color: oklch(42% 0.13 238);
    background: oklch(97% 0.01 238);
  }
}

@media (max-width: 1080px) {
  .workspace-header,
  .header-actions {
    flex-direction: column;
  }

  .workspace-grid,
  .task-panel {
    display: block;
  }

  .platform-panel,
  .task-panel {
    margin-top: 18px;
  }
}

@media (max-width: 720px) {
  .status-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .flow-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .upload-row,
  .split-fields,
  .platform-row {
    grid-template-columns: 1fr;
  }

  .target-options {
    padding-left: 0;
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
