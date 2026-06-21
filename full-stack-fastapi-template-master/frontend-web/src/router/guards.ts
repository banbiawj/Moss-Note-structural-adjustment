import type { NavigationGuard } from "vue-router"

const tokenStorageKey = "access_token"

export const requireAuth: NavigationGuard = () => {
  const accessToken = localStorage.getItem(tokenStorageKey)

  if (!accessToken) {
    return { name: "login" }
  }

  return true
}
