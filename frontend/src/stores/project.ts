import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getProjects } from '@/api/project'

interface Project {
  id: number
  name: string
  description: string | null
  environment: string
  owner_id: number
  is_active: boolean
  created_at: string
}

export const useProjectStore = defineStore('project', () => {
  const projects = ref<Project[]>([])
  const currentProject = ref<Project | null>(null)

  async function fetchProjects() {
    projects.value = await getProjects()
    // Restore current project from localStorage
    const savedId = localStorage.getItem('currentProjectId')
    if (savedId && !currentProject.value) {
      const found = projects.value.find((p) => p.id === Number(savedId))
      if (found) currentProject.value = found
    }
  }

  function setCurrentProject(project: Project) {
    currentProject.value = project
    localStorage.setItem('currentProjectId', String(project.id))
  }

  return { projects, currentProject, fetchProjects, setCurrentProject }
})
