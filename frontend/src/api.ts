import axios from 'axios';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : ''),
  timeout: 60000,
});

const ACADEMIC_MUTATION_PREFIXES = [
  '/courses/',
  '/classrooms/',
  '/subjects/',
  '/teachers/',
];

api.interceptors.response.use(
  response => {
    const method = response.config.method?.toLowerCase();
    const url = response.config.url || '';

    const isMutation =
      method === 'post'
      || method === 'put'
      || method === 'patch'
      || method === 'delete';

    const changesAcademicData =
      isMutation
      && ACADEMIC_MUTATION_PREFIXES.some(prefix =>
        url.startsWith(prefix),
      );

    if (changesAcademicData) {
      window.dispatchEvent(
        new CustomEvent('anatinus:academic-data-changed'),
      );
    }

    return response;
  },
  error => Promise.reject(error),
);
