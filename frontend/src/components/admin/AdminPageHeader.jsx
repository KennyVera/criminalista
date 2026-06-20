import PageHeader from '../layout/PageHeader'

export default function AdminPageHeader({ title, subtitle, icon, children, dataset }) {
  return (
    <PageHeader
      title={title}
      subtitle={subtitle}
      icon={icon}
      dataset={dataset}
      actions={children}
    />
  )
}
