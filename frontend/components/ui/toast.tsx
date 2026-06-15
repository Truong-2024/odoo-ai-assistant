import { toast } from 'sonner';

export const showToast = {
  success: (message: string) => {
    toast.success(message, {
      duration: 3000,
    });
  },

  error: (message: string) => {
    toast.error(message, {
      duration: 4000,
    });
  },

  info: (message: string) => {
    toast.info(message);
  },

  loading: (message: string) => {
    return toast.loading(message);
  },

  dismiss: (id?: string) => {
    toast.dismiss(id);
  }
};