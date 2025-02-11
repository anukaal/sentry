import EventView, {ImmutableEventView} from 'app/utils/discover/eventView';

import {createDefinedContext} from './utils';

type usePerformanceEventViewContext = {
  eventView: EventView;
};

const [PerformanceEventViewProvider, _usePerformanceEventView] =
  createDefinedContext<usePerformanceEventViewContext>({
    name: 'PerformanceEventViewContext',
  });

export {PerformanceEventViewProvider};

// Provides a readonly event view. Also omits anything that isn't currently read-only, although in the future we should switch the code in EventView instead.
// If you need mutability, use the mutable version.
export function usePerformanceEventView(): ImmutableEventView {
  return _usePerformanceEventView().eventView;
}

export function useMutablePerformanceEventView() {
  return usePerformanceEventView().clone();
}
