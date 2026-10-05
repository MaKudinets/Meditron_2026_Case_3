export const state = {
  result: null,
  cachedHistory: [],
  formDraft: null,
  busy: false,
  routeVersion: 0,
};
export function beginRoute() {
  state.routeVersion++;
}
