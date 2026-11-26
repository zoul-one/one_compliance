<template>
    <div class="employee-dashboard">
        <!-- Employee toolbar -->
        <EmployeeToolbar />

        <ProjectStatusCards />

        <!-- Bottom workspace: Projects, Tasks and Notifications / To-Do -->
        <div class="dashboard-workspace">
            <ProjectWorkspace />
            <NotificationsTodo />
        </div>
    </div>
</template>

<script setup>
import EmployeeToolbar from '../components/EmployeeToolbar.vue'
import ProjectStatusCards from '../components/ProjectStatusCards.vue'
import ProjectWorkspace from '../components/ProjectWorkspace.vue'
import NotificationsTodo from '../components/NotificationsTodo.vue'
</script>

<style scoped>

.employee-dashboard {
    width: 100%;
    min-height: 100%;
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

/* Employee Toolbar spacing */
.employee-dashboard > :first-child {
    margin-bottom: 30px;
}

/* Align sections consistently */
.employee-dashboard > :not(:first-child) {
    margin-left: 16px;
    width: calc(100% - 32px);
    box-sizing: border-box;
}

/* Bottom workspace: 4-column proportion */
.dashboard-workspace {
    position: relative;
    display: grid;
    grid-template-columns:
        minmax(0, 1.5fr)
        minmax(0, 1.5fr)
        minmax(0, 1fr);
    gap: 16px;
    padding-bottom: 20px;
    align-items: stretch;
    min-width: 0;
}

/* Expose Projects and Tasks as grid items */
.dashboard-workspace :deep(.workspace-grid) {
    display: contents;
}

/* Consistent panel sizing */
.dashboard-workspace :deep(.workspace-panel),
.dashboard-workspace :deep(.activity-panel) {
    width: 100%;
    min-width: 0;
    box-sizing: border-box;
}

/* Tablet layout */
@media (max-width: 1100px) {
    .dashboard-workspace {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .dashboard-workspace :deep(.activity-panel) {
        grid-column: 1 / -1;
    }
}

/* Mobile layout */
@media (max-width: 650px) {
    .dashboard-workspace {
        grid-template-columns: minmax(0, 1fr);
    }

    .dashboard-workspace :deep(.activity-panel) {
        grid-column: auto;
    }
}

</style>
