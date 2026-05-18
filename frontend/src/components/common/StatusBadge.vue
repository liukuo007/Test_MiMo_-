<template>
  <el-tag :type="type" :size="size">{{ label }}</el-tag>
</template>

<script setup lang="ts">
defineProps<{
  label: string
  type?: 'success' | 'warning' | 'danger' | 'info'
  size?: 'small' | 'default' | 'large'
}>()
</script>
