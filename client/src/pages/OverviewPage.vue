<template>
  <div class="overview">
    <MissedTaskExecutions />

    <IncompleteTasks />

    <Schedule />
  </div>
</template>
<script>
import Api from '@/api/Api'
import IncompleteTasks from '@/components/IncompleteTasks'
import MissedTaskExecutions from '@/components/MissedTaskExecutions'
import Schedule from '@/components/Schedule'

export default {
  name: 'OverviewPage',
  components: {
    IncompleteTasks,
    MissedTaskExecutions,
    Schedule
  },
  created: function () {
    Api.getAuth().then((auth) => {
      if (!auth) {
        this.$router.push('/login')
      }
    })
  }
}
</script>
