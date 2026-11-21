
import { mountVueIsland } from "@framework/ui/island";
import EmployeeDashboard from "../pages/EmployeeDashboard.vue";

export const mount = (el, context) =>
    mountVueIsland(el, {
        ...context,
        component: EmployeeDashboard
    });
