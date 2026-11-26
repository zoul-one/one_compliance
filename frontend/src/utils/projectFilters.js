export function isProjectWorking(project) {
    const allTasksCompleted =
        Number(project.total_tasks ?? project.totalTasks ?? 0) > 0 &&
        Number(project.completed_tasks ?? project.completedTasks ?? 0) >=
            Number(project.total_tasks ?? project.totalTasks ?? 0)

    const hasWorkingOrCompletedTask =
        (project.tasks?.some(task =>
            ['Working', 'Completed'].includes(task.status)
        ) ?? false) || Boolean(project.has_working_or_completed_task)

    return (
        ['Open', 'Overdue'].includes(project.status) &&
        hasWorkingOrCompletedTask &&
        !allTasksCompleted
    )
}

export function isProjectCompleted(project) {
    const totalTasks = Number(
        project.total_tasks ?? project.totalTasks ?? 0
    )
    const completedTasks = Number(
        project.completed_tasks ?? project.completedTasks ?? 0
    )

    return (
        ['Completed', 'Paid'].includes(project.status) ||
        (totalTasks > 0 && completedTasks >= totalTasks)
    )
}

export function matchesProjectFilter(project, filter) {
    switch (filter) {
        case 'All':
            return true
        case 'Working':
            return isProjectWorking(project)
        case 'Completed':
            return isProjectCompleted(project)
        case 'On Hold / Cancelled':
            return ['On Hold', 'Cancelled'].includes(project.status)
        case 'Overdue':
            return project.status === 'Overdue'
        default:
            return project.status === filter
    }
}

