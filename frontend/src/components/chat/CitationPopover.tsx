/** Citation popover — displays document source info for a citation badge. */

import * as Popover from "@radix-ui/react-popover";

interface CitationPopoverProps {
  index: number;
  documentName: string;
  page: number | string;
  textPreview: string;
}

export function CitationPopover({
  index,
  documentName,
  page,
  textPreview,
}: CitationPopoverProps) {
  return (
    <Popover.Root>
      <Popover.Trigger asChild>
        <button
          type="button"
          className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-800 rounded-full hover:bg-blue-200 transition-colors cursor-pointer"
        >
          [{index}]
        </button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content
          className="z-50 w-72 rounded-lg border border-gray-200 bg-white p-4 shadow-lg animate-in fade-in-0 zoom-in-95 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95"
          sideOffset={4}
        >
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-gray-900 truncate">
                {documentName}
              </span>
              <span className="text-xs text-gray-500">Página {page}</span>
            </div>
            <p className="text-xs text-gray-600 leading-relaxed line-clamp-3">
              {textPreview}
            </p>
          </div>
          <Popover.Arrow className="fill-white" />
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}
