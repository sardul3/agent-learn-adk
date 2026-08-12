import type { Theme } from 'vitepress'
import DefaultTheme from 'vitepress/theme-without-fonts'
import Layout from './Layout.vue'
import PackBoard from './components/PackBoard.vue'
import ContinueLane from './components/ContinueLane.vue'
import PackDetail from './components/PackDetail.vue'
import './custom.css'

export default {
  extends: DefaultTheme,
  Layout,
  enhanceApp({ app }) {
    app.component('PackBoard', PackBoard)
    app.component('ContinueLane', ContinueLane)
    app.component('PackDetail', PackDetail)
  },
} satisfies Theme
