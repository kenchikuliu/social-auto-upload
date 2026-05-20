import { http } from '@/utils/request'

export const platformApi = {
  getPlatforms() {
    return http.get('/v1/platforms')
  },

  getAccounts() {
    return http.get('/v1/accounts')
  },

  loginAccount(data) {
    return http.post('/v1/accounts/login', data)
  },

  checkAccount(data) {
    return http.post('/v1/accounts/check', data)
  },

  getMaterials() {
    return http.get('/v1/materials')
  },

  uploadMaterial(formData, onUploadProgress) {
    return http.upload('/v1/materials', formData, onUploadProgress)
  },

  publish(data) {
    return http.post('/v1/publish', data)
  },

  getJob(jobId) {
    return http.get(`/v1/jobs/${jobId}`)
  },

  getJobs() {
    return http.get('/v1/jobs')
  }
}
