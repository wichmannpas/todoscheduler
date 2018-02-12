<template>
  <div>
    <a
        @click="modalActive=true">
      New Task
    </a>

    <NewTaskModal
        @close="modalActive = false"
        v-if="modalActive"
    />
  </div>
</template>

<script>
import NewTaskModal from '@/components/NewTaskModal'

export default {
  name: 'NewTask',
  data: function () {
    return {
      modalActive: false
    }
  },
  components: {
    NewTaskModal
  }
}
</script>
