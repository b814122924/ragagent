<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { submitTask } from '../api/tasks'

const router = useRouter()
const topic = ref('')
const submitting = ref(false)

async function onSubmit() {
  const value = topic.value.trim()
  if (!value) {
    ElMessage.warning('请输入研究主题')
    return
  }
  if (submitting.value) return
  submitting.value = true
  try {
    const result = await submitTask(value)
    ElMessage.success(`任务已提交：${result.task_id}`)
    router.push(`/tasks/${result.task_id}`)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '提交失败，请检查后端服务')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="home-page">
    <div class="hero">
      <h2>多智能体报告生成</h2>
      <p class="hint">
        输入研究主题，系统将自动规划执行步骤（Plan-and-Execute），
        由 Researcher 联网搜索数据、Writer 撰写报告草稿，全程可视化展示 ReAct 推理过程
      </p>
    </div>

    <el-card shadow="never" class="submit-card">
      <el-input
        v-model="topic"
        type="textarea"
        :rows="3"
        maxlength="200"
        show-word-limit
        placeholder="例如：智能手表 2025 市场分析、便携式储能电源 北美市场 2026…"
        @keydown.enter.exact.prevent="onSubmit"
      />
      <div class="submit-actions">
        <el-button type="primary" size="large" :loading="submitting" @click="onSubmit">
          生成研究报告
        </el-button>
        <el-button size="large" @click="router.push('/tasks')">历史任务</el-button>
      </div>
    </el-card>

    <el-row :gutter="16" class="feature-row">
      <el-col :span="8">
        <el-card shadow="hover" class="feature-card">
          <h3>Plan 规划</h3>
          <p class="hint">Planner Agent 将主题拆解为多步执行计划（含依赖关系）</p>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="feature-card">
          <h3>ReAct 搜索</h3>
          <p class="hint">Researcher 通过 Thought→Action→Observation 循环联网搜索数据</p>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="feature-card">
          <h3>Writer 撰写</h3>
          <p class="hint">Writer 基于研究数据生成结构化报告草稿</p>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.home-page {
  max-width: 960px;
  margin: 0 auto;
}
.hero {
  text-align: center;
  margin-bottom: 24px;
}
.hero h2 {
  margin: 0 0 8px;
  font-size: 24px;
}
.hint {
  color: #909399;
  font-size: 13px;
  line-height: 20px;
}
.submit-card {
  margin-bottom: 24px;
}
.submit-actions {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
.feature-row .el-col {
  display: flex;
}
.feature-card {
  flex: 1;
}
.feature-row h3 {
  margin: 0 0 8px;
  font-size: 15px;
}
</style>
