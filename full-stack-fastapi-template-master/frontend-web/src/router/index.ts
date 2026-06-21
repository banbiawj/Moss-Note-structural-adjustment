import { createRouter, createWebHistory } from "vue-router"

import AppShell from "../layouts/AppShell.vue"
import EmptyLayout from "../layouts/EmptyLayout.vue"
import EditorPage from "../pages/EditorPage.vue"
import LibraryPage from "../pages/LibraryPage.vue"
import LoginPage from "../pages/LoginPage.vue"
import NotFoundPage from "../pages/NotFoundPage.vue"
import { requireAuth } from "./guards"

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      redirect: "/library",
    },
    {
      path: "/",
      component: AppShell,
      beforeEnter: requireAuth,
      children: [
        {
          path: "library",
          name: "library",
          component: LibraryPage,
        },
        {
          path: "editor",
          name: "editor",
          component: EditorPage,
        },
      ],
    },
    {
      path: "/login",
      component: EmptyLayout,
      children: [
        {
          path: "",
          name: "login",
          component: LoginPage,
        },
      ],
    },
    {
      path: "/:pathMatch(.*)*",
      name: "not-found",
      component: NotFoundPage,
    },
  ],
})
