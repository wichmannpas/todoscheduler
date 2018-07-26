<template>
  <form
      @submit.prevent="login">
    <div class="form-group">
      <label class="form-label" for="login-username">
        Username
      </label>
      <input
          id="login-username"
          type="text" class="form-input"
          placeholder="Username"
          v-model="user.username"
          @keydown="authFailure = false" />
    </div>
    <div class="form-group">
      <label class="form-label" for="loginform-password">
        Password
      </label>
      <input
          id="loginform-password"
          type="password" class="form-input"
          placeholder="Password"
          v-model="user.password"
          @keydown="authFailure = false" />
    </div>
    <div
        class="loading loading-lg"
        v-if="loading">
    </div>
    <div
        class="toast toast-warning"
        v-if="authFailure">
      Login with username “<em>{{ user.username }}</em>” failed.
    </div>

    <input type="submit" class="btn btn-primary" value="Login" />
    <a href="/accounts/register/">
      Register
    </a>
  </form>
</template>

<script>
import Api from '@/api/Api'

export default {
  name: 'LoginForm',
  data: function () {
    return {
      authFailure: false,
      loading: false,
      user: {
        username: '',
        password: ''
      }
    }
  },
  created: function () {
    Api.getAuth().then((auth) => {
      if (auth) {
        this.$router.push('/')
      }
    })
  },
  methods: {
    login () {
      this.authFailure = false
      this.loading = true
      Api.login(this.user.username, this.user.password).then(
        () => {
          this.authFailure = false
          console.log('successfully authenticated')
          this.$router.push('/')
        }).catch(
        (error) => {
          if (error) {
            console.error(error)
            this.authFailure = true
          }
        }).finally(() => {
        this.loading = false
      })
    }
  }
}
</script>
