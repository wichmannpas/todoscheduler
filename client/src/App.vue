<template>
  <div class="app">
    <div class="container">
      <router-view>
      </router-view>
    </div>
  </div>
</template>

<script>
import LoginForm from './components/LoginForm'

export default {
  name: 'App',
  components: {
    LoginForm
  }
}
</script>
