import { useUserStore } from '@/stores/user'

export function useAuth() {
  const userStore = useUserStore()

  function isLoggedIn() {
    return !!userStore.token
  }

  function hasRole(role: string) {
    return userStore.userInfo?.role === role
  }

  function isAdmin() {
    return hasRole('admin')
  }

  return { isLoggedIn, hasRole, isAdmin }
}
