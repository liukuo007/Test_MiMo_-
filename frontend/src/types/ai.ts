export interface AIModel {
  id: number
  name: string
  model_type: string
  created_at: string
}

export interface AIEvaluation {
  id: number
  model_version_id: number
  dataset_name: string
  accuracy: number | null
  recall: number | null
  f1_score: number | null
  total_samples: number
  created_at: string
}
