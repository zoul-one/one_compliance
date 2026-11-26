<template>
    <section class="activity-panel">
        <!-- COMBINED HEADER AND TAB SWITCHER -->
        <div class="activity-header" >
            <div class="activity-heading">
                <h3>
                    {{ activeTab === 'notifications' ? 'Notifications' : 'My To-Do' }}
                </h3>
            </div>
            <div class="activity-tabs">
                <TabButtons
                    v-model="activeTab"
                    :options="activityTabOptions"
                />
            </div>
        </div>
        <!-- NOTIFICATIONS -->
        <div
            v-if="activeTab === 'notifications'"
            class="activity-list" data-tour="notifications"
        >
            <!-- NOTIFICATION OVERVIEW -->
            <div class="notification-toolbar">
                <div class="notification-summary">
                    <Badge theme="blue">
                        {{ unreadCount }}
                    </Badge>
                    <span>Unread notifications</span>
                </div>
                <Button
                    variant="ghost"
                    theme="gray"
                    size="sm"
                    :disabled="unreadCount === 0"
                    @click="markAllAsRead"
                >
                    <template #prefix>
                        <Icon name="lucide-check-check" />
                    </template>
                    Mark all as read
                </Button>
            </div>
            <!-- NOTIFICATION ITEMS -->
            <div
                v-for="notification in notifications"
                :key="notification.id"
                class="notification-item"
                :class="{ unread: !notification.read }"
                @click="markAsRead(notification)"
            >
                <div class="notification-icon-wrapper">
                    <div
                        class="notification-type-icon"
                        :class="notification.iconClass"
                    >
                        <Icon :name="notification.icon" />
                    </div>
                </div>
                <div class="notification-content">
                    <div class="notification-title-row">
                        <span class="notification-title">
                            {{ notification.title }}
                        </span>
                        <span
                            v-if="!notification.read"
                            class="unread-indicator"
                            title="Unread"
                        ></span>
                    </div>
                    <div class="notification-meta">
                        <span>{{ notification.source }}</span>
                        <span class="meta-separator">·</span>
                        <span>{{ notification.time }}</span>
                    </div>
                </div>
            </div>
            <div
                v-if="!notifications.length"
                class="activity-empty-state"
            >
                <Icon name="lucide-bell-off" />
                <span>No notifications available</span>
            </div>
        </div>
        <!-- TO-DO -->
        <div
            v-else
            class="activity-list todo-list"
            data-tour="to-do-list"
        >
            <!-- TODO OVERVIEW -->
            <div class="todo-toolbar">
                <div class="todo-summary">
<button
                        type="button"
                        class="todo-filter-badge todo-filter-pending"
                        :class="{ active: activeTodoFilter === 'Pending' }"
                        @click="activeTodoFilter = 'Pending'"
                    >
                        {{ pendingTasksCount }} Pending
                    </button>
                    <button
                        type="button"
                        class="todo-filter-badge todo-filter-overdue"
                        :class="{ active: activeTodoFilter === 'Overdue' }"
                        @click="activeTodoFilter = 'Overdue'"
                    >
                        {{ overdueTasksCount }} Overdue
                    </button>
                    <div class="todo-priority-control">
                        <button
                            type="button"
                            class="todo-priority-trigger"
                            @click="showPriorityMenu = !showPriorityMenu"
                            :aria-expanded="showPriorityMenu"
                        >
                            Priority
                            <Icon name="lucide-chevron-down" />
                        </button>
                        <div v-if="showPriorityMenu" class="todo-priority-menu">
                            <button
                                v-for="priority in ['All', 'Low', 'Medium', 'High']"
                                :key="priority"
                                type="button"
                                :class="{ selected: activePriorityFilter === priority }"
                                @click="
                                    activePriorityFilter = priority;
                                    showPriorityMenu = false
                                "
                            >
                                {{ priority }}
                            </button>
                        </div>
                    </div>
                </div>

            </div>
            <!-- TASK ITEMS -->
            <div
                v-for="task in filteredTodoTasks"
                :key="task.id"
                class="todo-item"
                :class="{ 'todo-completed': task.completed }"
            >
                <div class="todo-checkbox-wrapper">
                    <input
                        type="checkbox"
                        :id="`todo-${task.id}`"
                        :checked="task.completed"
                        :disabled="task.status === 'Cancelled'"
                        @change="toggleTask(task)"
                    />
                </div>
                <div class="todo-content">
                    <label
                        :for="`todo-${task.id}`"
                        class="todo-description"
                    >
                        {{ task.description }}
                    </label>
                    <div class="todo-meta">
                        <span class="todo-deadline">
                            <Icon name="lucide-calendar-days" />
                            {{ formatDeadline(task.deadline) }}
                        </span>
                        <span
                            class="todo-status-badge"
                            :class="taskStatusClass(task)"
                        >
                            {{ taskStatus(task) }}
                        </span>
                        <span
                            class="todo-priority-badge"
                            :class="priorityClass(task.priority)"
                        >
                            {{ task.priority }} Priority
                        </span>
                    </div>
                </div>
                <Button
                    v-if="task.status !== 'Closed'"
                    variant="ghost"
                    theme="gray"
                    size="sm"
                    class="edit-task-button"
                    title="Edit task"
                    @click="openEditTask(task)"
                >
                    <template #prefix>
                        <Icon name="lucide-pencil" />
                    </template>
                </Button>
            </div>
            <div
                v-if="!filteredTodoTasks.length"
                class="activity-empty-state"
            >
                <Icon name="lucide-clipboard-check" />
                <span>No tasks available for the selected filters</span>
            </div>
        </div>
        <!-- EDIT TASK POPUP -->
        <div
            v-if="showEditTask"
            class="todo-modal-backdrop"
            @click.self="closeEditTask"
        >
            <section class="todo-modal">
                <div class="todo-modal-header">
                    <div>
                        <h3>Edit Task</h3>
                        <p>Update your task details</p>
                    </div>
                    <Button
                        variant="ghost"
                        theme="gray"
                        size="sm"
                        @click="closeEditTask"
                    >
                        <template #prefix>
                            <Icon name="lucide-x" />
                        </template>
                    </Button>
                </div>
                <div class="todo-modal-body">
                    <FormControl
                        v-model="editingTask.description"
                        type="textarea"
                        label="Task Description"
                        placeholder="Enter task description"
                        :rows="3"
                        required
                    />
                    <FormControl
                        v-model="editingTask.deadline"
                        type="date"
                        label="Deadline"
                        required
                    />
                    <FormControl
                        v-model="editingTask.priority"
                        type="select"
                        label="Priority"
                        :options="[
                            { label: 'High', value: 'High' },
                            { label: 'Medium', value: 'Medium' },
                            { label: 'Low', value: 'Low' }
                        ]"
                    />
                </div>
                <div class="todo-modal-footer">
                    <Button
                        variant="outline"
                        theme="gray"
                        @click="closeEditTask"
                    >
                        Cancel
                    </Button>
                    <Button
                        variant="solid"
                        theme="green"
                        :disabled="
                            !editingTask.description.trim() ||
                            !editingTask.deadline
                        "
                        @click="saveTask"
                    >
                        Save Changes
                    </Button>
                </div>
            </section>
        </div>
    </section>
</template>
<script setup>
import { computed, reactive, ref, onMounted } from 'vue'
import { Badge, Button, Icon, FormControl, TabButtons } from 'frappe-ui'
// ==================================================
// ACTIVE TAB
// ==================================================
const activeTab = ref('notifications')
const activityTabOptions = computed(() => [
    {
        label: unreadCount.value
            ? `Notifications (${unreadCount.value})`
            : 'Notifications',
        value: 'notifications',
    },
    {
        label: pendingTasksCount.value
            ? `To-Do (${pendingTasksCount.value})`
            : 'To-Do',
        value: 'todo',
    },
])
// ==================================================
// NOTIFICATIONS - FRAPPE API
// ==================================================
const notifications = ref([])
const unreadCount = computed(() =>
    notifications.value.filter(item => !item.read).length
)
// Convert Frappe notification/ToDo HTML into safe, readable plain text.
// DOMParser also decodes entities such as & and <.
function toPlainText(value) {
    if (!value) return ''
    const parsed = new DOMParser().parseFromString(String(value), 'text/html')
    return (parsed.body.textContent || '')
        .replace(/\s+/g, ' ')
        .trim()
}
// Convert Frappe's creation timestamp into readable relative time.
function formatNotificationTime(value) {
    if (!value) return ''
    const date = new Date(String(value).replace(' ', 'T'))
    if (Number.isNaN(date.getTime())) return ''
    const minutes = Math.floor((Date.now() - date.getTime()) / 60000)
    if (minutes < 1) return 'Just now'
    if (minutes < 60) return `${minutes} minutes ago`
    const hours = Math.floor(minutes / 60)
    if (hours < 24) return `${hours} hours ago`
    if (hours < 48) return 'Yesterday'
    const days = Math.floor(hours / 24)
    return `${days} days ago`
}
// Map Frappe notification records to the existing UI format.
function formatNotification(record) {
    const documentType = record.document_type || record.source_doctype || ''
    let source = 'General'
    let icon = 'lucide-bell'
    let iconClass = 'notification-purple'
    if (documentType === 'Task') {
        source = 'Task Management'
        icon = 'lucide-list-checks'
        iconClass = 'notification-blue'
    } else if (documentType === 'Project') {
        source = 'Project Management'
        icon = 'lucide-folder-kanban'
        iconClass = 'notification-green'
    } else if (documentType === 'User') {
        source = 'Account'
        icon = 'lucide-user-round'
        iconClass = 'notification-purple'
    }
    // Both title and description may contain HTML markup/entities.
    const title = toPlainText(record.title) || 'Notification'
    const message = toPlainText(record.description)
    return {
        id: record.name,
        title,
        message,
        source,
        time: formatNotificationTime(record.creation),
        icon,
        iconClass,
        read: Boolean(record.read),
    }
}
// Load notifications belonging to the logged-in user.
async function loadNotifications() {
    try {
        const response = await fetch(
            '/api/method/one_compliance.one_compliance.api.executive_dashboard.get_my_notifications',
            {
                method: 'GET',
                credentials: 'same-origin',
            }
        )
        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status}`)
        }
        const result = await response.json()
        notifications.value = (result.message || []).map(formatNotification)
    } catch (error) {
        console.error('Failed to load notifications:', error)
    }
}
// Mark an individual notification as read.
async function markAsRead(notification) {
    if (notification.read) return
    try {
        const response = await fetch(
            '/api/method/one_compliance.one_compliance.api.executive_dashboard.mark_notification_as_read',
            {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-Frappe-CSRF-Token': window.frappe.csrf_token,
                },
                body: new URLSearchParams({
                    notification_name: notification.id,
                }),
            }
        )
        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status}`)
        }
        const result = await response.json()
        if (result.message?.success) {
            notification.read = true
        }
    } catch (error) {
        console.error('Failed to mark notification as read:', error)
    }
}
// Mark all notifications as read.
async function markAllAsRead() {
    if (unreadCount.value === 0) return
    try {
        const response = await fetch(
            '/api/method/one_compliance.one_compliance.api.executive_dashboard.mark_all_notifications_as_read',
            {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-Frappe-CSRF-Token': window.frappe.csrf_token,
                },
            }
        )
        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status}`)
        }
        const result = await response.json()
        if (result.message?.success) {
            notifications.value.forEach(notification => {
                notification.read = true
            })
        }
    } catch (error) {
        console.error('Failed to mark all notifications as read:', error)
    }
}
// Load notifications when the component is mounted.
onMounted(() => {
    loadNotifications()
    loadTodos()
})
// ==================================================
// TO-DO - FRAPPE API
// ==================================================
const todoTasks = ref([])
// Convert Frappe ToDo records into the existing UI format.
function formatTodo(record) {
    const description = toPlainText(record.description)
    return {
        id: record.name,
        description,
        deadline: record.date || '',
        priority: record.priority || 'Medium',
        status: record.status,
        completed: record.status === 'Closed',
    }
}
// Load ToDo records assigned to the logged-in user.
async function loadTodos() {
    try {
        const response = await fetch(
            '/api/method/one_compliance.one_compliance.api.executive_dashboard.get_my_todos',
            {
                method: 'GET',
                credentials: 'same-origin',
            }
        )
        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status}`)
        }
        const result = await response.json()
        todoTasks.value = (result.message || []).map(formatTodo)
    } catch (error) {
        console.error('Failed to load ToDo records:', error)
    }
}
const pendingTasksCount = computed(() =>
    todoTasks.value.filter(task => task.status === 'Open').length
)

const overdueTasksCount = computed(() =>
    todoTasks.value.filter(task => taskStatus(task) === 'Overdue').length
)
// ==================================================
// TODO FILTERS
// ==================================================
const activeTodoFilter = ref('Pending')
const activePriorityFilter = ref('All')
const showPriorityMenu = ref(false)
const filteredTodoTasks = computed(() => {
    let result = todoTasks.value
    if (activeTodoFilter.value === 'Pending') {
        result = result.filter(task => task.status === 'Open')
    } else if (activeTodoFilter.value === 'Overdue') {
        result = result.filter(task => taskStatus(task) === 'Overdue')
    }
    if (activePriorityFilter.value !== 'All') {
        result = result.filter(task => task.priority === activePriorityFilter.value)
    }
    return result
})
// ==================================================
// TASK STATUS AND DEADLINE HELPERS
// ==================================================
function getTodayDate() {
    const now = new Date()
    const year = now.getFullYear()
    const month = String(now.getMonth() + 1).padStart(2, '0')
    const day = String(now.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
}
function taskStatus(task) {
    if (task.status === 'Cancelled') {
        return 'Cancelled'
    }
    if (task.status === 'Closed') {
        return 'Completed'
    }
    const today = getTodayDate()
    if (task.deadline && task.deadline < today) {
        return 'Overdue'
    }
    if (task.deadline === today) {
        return 'Due Today'
    }
    return 'Active'
}
function taskStatusClass(task) {
    return {
        'status-completed': task.status === 'Closed',
        'status-cancelled': task.status === 'Cancelled',
        'status-overdue': task.status === 'Open' && taskStatus(task) === 'Overdue',
        'status-due-today': task.status === 'Open' && taskStatus(task) === 'Due Today',
        'status-active': task.status === 'Open' && taskStatus(task) === 'Active',
    }
}
function priorityClass(priority) {
    if (priority === 'High') return 'priority-high'
    if (priority === 'Medium') return 'priority-medium'
    return 'priority-low'
}
function formatDeadline(date) {
    if (!date) return ''
    const parsedDate = new Date(`${date}T00:00:00`)
    return parsedDate.toLocaleDateString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
    })
}
// ==================================================
// COMPLETE TASK
// ==================================================
function toggleTask(task) {
    task.completed = !task.completed
}
// ==================================================
// EDIT TASK POPUP
// ==================================================
const showEditTask = ref(false)
const editingTask = reactive({
    id: null,
    description: '',
    deadline: '',
    priority: 'Low',
})
function openEditTask(task) {
    editingTask.id = task.id
    editingTask.description = task.description
    editingTask.deadline = task.deadline
    editingTask.priority = task.priority
    showEditTask.value = true
}
function closeEditTask() {
    showEditTask.value = false
}
async function saveTask() {
    const task = todoTasks.value.find(
        item => item.id === editingTask.id
    )
    if (!task) return
    const description = editingTask.description.trim()
    if (!description || !editingTask.deadline) return
    try {
        const response = await fetch(
            '/api/method/one_compliance.one_compliance.api.executive_dashboard.update_my_todo_details',
            {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-Frappe-CSRF-Token': window.frappe.csrf_token,
                },
                body: new URLSearchParams({
                    todo_name: editingTask.id,
                    description,
                    date: editingTask.deadline,
                    priority: editingTask.priority,
                }),
            }
        )
        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status}`)
        }
        const result = await response.json()
        if (result.message?.success) {
            task.description = description
            task.deadline = editingTask.deadline
            task.priority = editingTask.priority
            closeEditTask()
        }
    } catch (error) {
        console.error('Failed to update ToDo details:', error)
    }
}
</script>
<style scoped>
/* ==================================================
   MAIN PANEL
\================================================== */
.activity-panel {
    height: 430px;
    width: 100%;
    min-width: 0;
    display: flex;
    flex-direction: column;
    background: var(--surface-card);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    overflow: hidden;
    box-shadow:
        0 1px 2px rgba(15, 23, 42, 0.035),
        0 4px 10px rgba(15, 23, 42, 0.045),
        0 10px 24px rgba(15, 23, 42, 0.035);
}
/* ==================================================
   COMBINED HEADER AND TABS
\================================================== */
.activity-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 13px 15px;
    min-height: 70px;
    box-sizing: border-box;
    background: var(--surface-card);
    border-bottom: 1px solid var(--border-color);
    flex-shrink: 0;
}
.activity-heading {
    min-width: 0;
}
.activity-header h3 {
    margin: 0;
    font-size: 14px;
    font-weight: 450;
    color: var(--text-color);
}
.activity-header p {
    margin: 4px 0 0;
    font-size: 11px;
    color: var(--text-muted);
}
.activity-tabs {
    display: flex;
    align-items: center;
    gap: 5px;
    flex-shrink: 0;
}
/* ==================================================
   SHARED SCROLLABLE AREA
\================================================== */
.activity-list {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    overflow-x: hidden;
    background: var(--surface-card);
    scrollbar-width: thin;
    scrollbar-color: #cbd5e1 transparent;
}
.activity-list::-webkit-scrollbar {
    width: 5px;
}
.activity-list::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 10px;
}
/* ==================================================
   NOTIFICATION OVERVIEW
\================================================== */
/* NOTIFICATION OVERVIEW */
.notification-toolbar {
    position: sticky;
    top: 0;
    z-index: 10;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    min-height: 40px;
    box-sizing: border-box;
    padding: 5px 14px;
    background: var(--surface-gray-2);
    border-bottom: 1px solid var(--border-color);
    flex-shrink: 0;
}
.notification-summary {
    display: flex;
    align-items: center;
    gap: 7px;
    font-size: 11px;
    color: #000000
}
.notification-toolbar :deep(button) {
    color: #2d2d2d !important;
    font-weight: 450;
}

.notification-toolbar :deep(button:disabled) {
    color: #9ca3af !important;
    cursor: not-allowed;
    opacity: 0.65;
}
/* ==================================================
   NOTIFICATION ITEMS
\================================================== */
.notification-item {
    display: flex;
    align-items: flex-start;
    gap: 11px;
    padding: 13px 14px;
    border-bottom: 1px solid var(--border-color);
    cursor: pointer;
    transition: background 0.15s ease;
}
.notification-item:hover {
    background: var(--surface-gray-2);
}
.notification-item.unread {
    background: #f8fbff;
}
.notification-item.unread:hover {
    background: #f0f6ff;
}
.notification-icon-wrapper {
    flex-shrink: 0;
    padding-top: 1px;
}
.notification-type-icon {
    width: 34px;
    height: 34px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 4px;
}
.notification-type-icon :deep(svg) {
    width: 16px;
    height: 16px;
}
.notification-blue {
    color: #2563eb;
    background: #eff6ff;
}
.notification-green {
    color: #16a34a;
    background: #f0fdf4;
}
.notification-orange {
    color: #d97706;
    background: #fffbeb;
}
.notification-purple {
    color: #7c3aed;
    background: #f5f3ff;
}
.notification-content {
    flex: 1;
    min-width: 0;
}
.notification-title-row {
    display: flex;
    align-items: center;
    gap: 7px;
}
.notification-title {
    font-size: 12px;
    font-weight: 450;
    color: var(--text-color);
}
.unread-indicator {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #2563eb;
    flex-shrink: 0;
}
.notification-meta {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-top: 6px;
    font-size: 10px;
    color: var(--text-muted);
}
.meta-separator {
    color: #9ca3af;
}
/* ==================================================
   TODO OVERVIEW
\================================================== */
.todo-toolbar {
    position: sticky;
    top: 0;
    z-index: 10;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    min-height: 40px;
    box-sizing: border-box;
    padding: 5px 14px;
    background: var(--surface-gray-2);
    border-bottom: 1px solid var(--border-color);
    flex-shrink: 0;
}
.todo-toolbar > * {
    position: relative;
    z-index: 1;
}
.todo-summary {
    display: flex;
    align-items: center;
    gap: 7px;
    flex-wrap: wrap;
}
.todo-filter-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 3px 7px;
    border: 1px solid;
    border-radius: 12px;
    font-family: inherit;
    font-size: 10px;
    line-height: 1.3;
    font-weight: 500;
    white-space: nowrap;
    cursor: pointer;
    transition: background 0.15s ease, border-color 0.15s ease;
}
.todo-filter-all {
    color: #1d4ed8;
    background: #eff6ff;
    border-color: #2563eb;
}
.todo-filter-pending {
    color: #b45309;
    background: #fffbeb;
    border-color: #d97706;
}
.todo-filter-overdue {
    color: #b91c1c;
    background: #fee2e2;
    border-color: #ef4444;
}
.todo-filter-badge.active {
    font-weight: 700;
    box-shadow: inset 0 0 0 1px currentColor;
}
.todo-filter-badge:hover {
    filter: brightness(0.96);
}
.todo-priority-control {
    position: relative;
    display: flex;
    align-items: center;
    white-space: nowrap;
}
.todo-priority-trigger {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    padding: 3px 9px;
    border: 1px solid #334155;
    border-radius: 20px;
    background: #ffffff;
    color: #1e293b;
    font-family: inherit;
    font-size: 10px;
    line-height: 1.3;
    font-weight: 600;
    white-space: nowrap;
    cursor: pointer;
}
.todo-priority-trigger:hover {
    background: #f1f5f9;
    border-color: #1e293b;
}
.todo-priority-trigger :deep(svg) {
    width: 12px;
    height: 12px;
}
.todo-priority-menu {
    position: absolute !important;
    display: flex;
    flex-direction: column;
    top: calc(100% + 5px);
    right: 0;
    z-index: 100;
    min-width: 110px;
    padding: 4px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.15);
}
.todo-priority-menu button {
    display: block;
    width: 100%;
    padding: 8px 10px;
    border: none;
    border-radius: 4px;
    background: transparent;
    color: #475569;
    text-align: left;
    font-family: inherit;
    font-size: 13px;
    cursor: pointer;
}
.todo-priority-menu button:hover {
    background: #f1f5f9;
}
.todo-priority-menu button.selected {
    background: #eff6ff;
    color: #2563eb;
    font-weight: 600;
}
.todo-hint {
    font-size: 10px;
    color: var(--text-muted);
}
/* ==================================================
   TODO ITEMS
\================================================== */
.todo-item {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 13px 14px;
    border-bottom: 1px solid var(--border-color);
    transition: background 0.15s ease;
}
.todo-item:hover {
    background: var(--surface-gray-2);
}
.todo-checkbox-wrapper {
    flex-shrink: 0;
    padding-top: 2px;
}
.todo-checkbox-wrapper input {
    width: 15px;
    height: 15px;
    margin: 0;
    accent-color: #16a34a;
    cursor: pointer;
}
.todo-content {
    flex: 1;
    min-width: 0;
}
.todo-description {
    display: block;
    font-size: 12px;
    line-height: 1.5;
    font-weight: 450;
    color: var(--text-color);
    cursor: pointer;
    overflow-wrap: anywhere;
}
.todo-completed .todo-description {
    color: var(--text-muted);
    text-decoration: line-through;
}
.todo-meta {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 7px;
    margin-top: 7px;
}
.todo-deadline {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 10px;
    color: var(--text-muted);
}
.todo-deadline :deep(svg) {
    width: 12px;
    height: 12px;
}
/* ==================================================
   STATUS AND PRIORITY BADGES
\================================================== */
.todo-status-badge,
.todo-priority-badge {
    display: inline-flex;
    align-items: center;
    padding: 3px 7px;
    border-radius: 20px;
    font-size: 9px;
    line-height: 1.2;
    font-weight: 600;
    white-space: nowrap;
}
.status-completed {
    color: #15803d;
    background: #dcfce7;
}
.status-overdue {
    color: #b91c1c;
    background: #fee2e2;
}
.status-due-today {
    color: #b45309;
    background: #fef3c7;
}
.status-active {
    color: #2563eb;
    background: #dbeafe;
}
.status-cancelled {
    color: #6b7280;
    background: #f3f4f6;
}
.priority-high {
    color: #b91c1c;
    background: #fee2e2;
}
.priority-medium {
    color: #b45309;
    background: #fef3c7;
}
.priority-low {
    color: #4b5563;
    background: #f3f4f6;
}
/* ==================================================
   EDIT TASK BUTTON
\================================================== */
.edit-task-button {
    flex-shrink: 0;
}
/* ==================================================
   EMPTY STATE
\================================================== */
.activity-empty-state {
    min-height: 150px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 9px;
    color: var(--text-muted);
    font-size: 11px;
}
.activity-empty-state :deep(svg) {
    width: 24px;
    height: 24px;
}
/* ==================================================
   EDIT TASK MODAL
\================================================== */
.todo-modal-backdrop {
    position: fixed;
    inset: 0;
    z-index: 1200;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
    background: rgba(15, 23, 42, 0.58);
}
.todo-modal {
    width: 100%;
    max-width: 460px;
    display: flex;
    flex-direction: column;
    max-height: 85vh;
    overflow: hidden;
    background: #ffffff;
    color: #1f2937;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    box-shadow: 0 18px 50px rgba(0, 0, 0, 0.25);
}
.todo-modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 18px 22px;
    border-bottom: 1px solid var(--border-color);
    background: var(--surface-card);
}
.todo-modal-header h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: var(--text-color);
}
.todo-modal-header p {
    margin: 5px 0 0;
    font-size: 12px;
    color: var(--text-muted);
}
.todo-modal-body {
    display: flex;
    flex-direction: column;
    gap: 15px;
    padding: 20px;
    overflow-y: auto;
    background: #ffffff;
}
.form-group {
    display: flex;
    flex-direction: column;
    gap: 7px;
}
.form-group label {
    font-size: 11px;
    font-weight: 600;
    color: #374151;
}
.form-group input,
.form-group select,
.form-group textarea {
    width: 100%;
    box-sizing: border-box;
    padding: 10px 11px;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    background: #ffffff;
    color: #1f2937;
    font-family: inherit;
    font-size: 12px;
    outline: none;
}
.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
    border-color: #93c5fd;
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.12);
}
.form-group textarea {
    resize: vertical;
    min-height: 75px;
}
.todo-modal-footer {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 8px;
    padding: 14px 20px;
    border-top: 1px solid #e5e7eb;
    background: #ffffff;
}
/* ==================================================
   RESPONSIVE
\================================================== */
@media (max-width: 500px) {
    .activity-header {
        align-items: flex-start;
        flex-direction: column;
        padding: 13px;
    }
    .activity-tabs {
        width: 100%;
    }
    .activity-tabs :deep(button) {
        flex: 1;
    }
    .notification-item,
    .todo-item {
        padding: 11px;
    }
    .todo-hint {
        display: none;
    }
    .todo-modal-backdrop {
        padding: 12px;
    }
    .todo-modal-header,
    .todo-modal-body {
        padding: 15px;
    }
}
</style>
