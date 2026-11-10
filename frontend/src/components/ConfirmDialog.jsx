import { useEffect, useRef } from 'react';

export default function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = 'Xác nhận xóa',
  busy = false,
  onCancel,
  onConfirm,
}) {
  const cancelRef = useRef(null);
  const dialogRef = useRef(null);
  const onCancelRef = useRef(onCancel);
  onCancelRef.current = onCancel;

  useEffect(() => {
    if (!open) return undefined;
    cancelRef.current?.focus();
    const handleKeyDown = (event) => {
      if (event.key === 'Escape' && !busy) onCancelRef.current?.();
      if (event.key === 'Tab') {
        const controls = dialogRef.current?.querySelectorAll('button:not(:disabled)') || [];
        if (controls.length < 2) return;
        const first = controls[0];
        const last = controls[controls.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [open, busy]);

  if (!open) return null;

  return (
    <div className="dialog-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget && !busy) onCancel(); }}>
      <section ref={dialogRef} className="confirm-dialog" role="alertdialog" aria-modal="true" aria-labelledby="confirm-dialog-title" aria-describedby="confirm-dialog-description">
        <span className="dialog-warning-icon" aria-hidden="true">!</span>
        <div className="confirm-dialog-copy">
          <h2 id="confirm-dialog-title">{title}</h2>
          <p id="confirm-dialog-description">{description}</p>
        </div>
        <div className="confirm-dialog-actions">
          <button ref={cancelRef} className="ghost-button" type="button" onClick={onCancel} disabled={busy}>Hủy</button>
          <button className="danger-button" type="button" onClick={onConfirm} disabled={busy}>{busy ? <><span className="button-spinner" aria-hidden="true" />Đang xóa...</> : confirmLabel}</button>
        </div>
      </section>
    </div>
  );
}
