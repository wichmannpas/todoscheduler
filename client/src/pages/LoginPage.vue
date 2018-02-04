<template>
  <div class="login">
    <h1>
      Login
    </h1>

    <LoginForm />
  </div>
</template>

<script>
import LoginForm from '@/components/LoginForm'

export default {
  name: 'Login',
  components: {
    LoginForm
  }
}
</script>
