<template>
  <div class="overview">
    overview
  </div>
</template>
<script>
import Api from '@/api/Api'

export default {
  name: 'OverviewPage',
  created: function () {
    Api.getAuth().then((auth) => {
      if (!auth) {
        this.$router.push('/login')
      }
    })
  }
}
</script>
