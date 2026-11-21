// Tour steps. Selectors point inside the island's shadow root.
const DASHBOARD_TOUR_STEPS = [
    {
        selector: '[data-tour="employee-profile"]',
        title: 'Your profile',
        description: 'Your name, ID and role.',
        position: 'bottom',
    },
];

function startDashboardTour(wrapper, { force = false } = {}) {
    const seenKey = `dashboard_tour_seen:${frappe.session.user}`;
    if (!force && localStorage.getItem(seenKey)) return;

    const root = wrapper.querySelector('.frappe-island')?.shadowRoot;
    if (!root) return;

    // Driver's highlight CSS lives in the main page, not in the shadow root.
    // Copy the bits that lift the highlighted element above the overlay.
    if (!root.querySelector('style[data-tour-css]')) {
        const style = document.createElement('style');
        style.dataset.tourCss = '1';
        style.textContent = `
            .driver-highlighted-element { z-index: 100004 !important; }
            .driver-position-relative { position: relative !important; }
            .driver-fix-stacking {
                z-index: auto !important;
                opacity: 1 !important;
                transform: none !important;
                filter: none !important;
                will-change: unset !important;
            }
        `;
        root.appendChild(style);
    }

    const steps = DASHBOARD_TOUR_STEPS
        .map(step => ({
            element: root.querySelector(step.selector),
            popover: {
                title: __(step.title),
                description: __(step.description),
                position: step.position,
            },
        }))
        .filter(step => step.element);

    if (!steps.length) return;

    const driver = new frappe.Driver({
        className: 'frappe-driver',
        allowClose: false,
        padding: 10,
        opacity: 0.5,
        nextBtnText: __('Next'),
        prevBtnText: __('Previous'),
        doneBtnText: __('Done'),
        closeBtnText: __('Skip'),
        onReset: () => localStorage.setItem(seenKey, '1'),
    });

    driver.defineSteps(steps);
    driver.start();
}

frappe.pages['employee-associate-dashboard'].on_page_load = function (wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: '',
        single_column: true
    });

    // Hide the redundant Desk page heading.
    $(wrapper).find('.page-head').hide();

    page.main.addClass('employee-associate-dashboard-page');

    // Create the container where the Vue Island will be mounted.
    const mountElement = document.createElement('div');
    mountElement.className = 'employee-associate-dashboard-island';

    page.body.empty().append(mountElement);

    // Mount the Vue Island.
    wrapper.employee_dashboard_island = frappe.ui.mount_island(
        'one_compliance.employee_dashboard',
        mountElement,
        {}
    );

    // Handle mounting errors.
    wrapper.employee_dashboard_island.ready.catch(error => {
        console.error('Employee Associate Dashboard failed to mount:', error);
    });

    wrapper.employee_dashboard_island.ready.then(() => {
        setTimeout(() => startDashboardTour(wrapper), 300);
    });
};