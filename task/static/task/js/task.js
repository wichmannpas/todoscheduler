(function () {
  /**
   * Close all modals.
   */
  function closeModals() {
    $('.modal').removeClass('active');
  }
  /**
   * Initialize and display the new task modal.
   */
  function initNewTask(event) {
    if (event !== undefined) {
      event.preventDefault();
    }
    let name = $('#new_task_name');
    name.val('');
    $('#new_task_duration').val(1);
    $('#new_task').addClass('active');

    name.focus();
  }

  $(function () {
    $('#new_task_link').click(initNewTask);
    $('.modal-close').click(closeModals);
    $('.modal-overlay').click(closeModals);
  });
})();