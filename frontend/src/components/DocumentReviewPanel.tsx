import React, { useState, useEffect, useMemo } from 'react'
import { Card, Tag, Button, Spin, Input, Select, message, Form, Empty, Divider, Radio } from 'antd'
import { CheckCircleOutlined, EditOutlined, CloseCircleOutlined, PlusOutlined, SaveOutlined, RollbackOutlined, RobotOutlined } from '@ant-design/icons'

// 模拟从后端获取的数据类型
interface ExtractedEntity {
  id: string
  text: string // 从原文中抽取的文本
  label: 'project_name' | 'manager' | 'company' | 'date' | 'amount' // 实体类型
  value: string | number // 归一化后的值
  status: 'pending' | 'confirmed' | 'rejected' // 人工审核状态
  context: string // 实体所在的原文上下文
}

// 1. 定义常量，便于维护和复用
const ENTITY_LABELS: Record<ExtractedEntity['label'], string> = {
  project_name: '项目名称',
  manager: '项目经理',
  company: '公司名称',
  date: '日期',
  amount: '金额',
};

const STATUS_CONFIG: Record<ExtractedEntity['status'], { color: string; text: string }> = {
  pending: { color: 'gold', text: '待审核' },
  confirmed: { color: 'success', text: '已确认' },
  rejected: { color: 'error', text: '已忽略' },
};

// 模拟 API 调用
const fetchExtractedEntities = async (documentId: string): Promise<ExtractedEntity[]> => {
  console.log(`Fetching entities for document ${documentId}...`)
  // 在实际应用中，这里会调用后端 API
  return new Promise((resolve) =>
    setTimeout(
      () =>
        resolve([
          { id: 'ent-1', text: '智慧城市大脑项目', label: 'project_name', value: '智慧城市大脑项目', status: 'pending', context: '...本次招标的智慧城市大脑项目旨在...' },
          { id: 'ent-2', text: '张三', label: 'manager', value: '张三', status: 'pending', context: '...项目经理应为张三...' },
          { id: 'ent-3', text: '预算：约500万', label: 'amount', value: 5000000, status: 'pending', context: '...项目总预算：约500万...' },
          { id: 'ent-4', text: '我方公司', label: 'company', value: '我方公司', status: 'confirmed', context: '...由我方公司负责实施...' },
        ]),
      1000
    )
  )
}

// 2. 模拟一个可能失败的API调用，以测试错误处理
const updateEntity = async (entityId: string, updates: Partial<ExtractedEntity>) => {
  console.log(`Updating entity ${entityId} with`, updates)
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      if (Math.random() > 0.8) { // 20% 概率失败
        reject(new Error('网络错误，保存失败'))
      } else {
        message.success('操作成功！')
        resolve(true)
      }
    }, 500)
  })
}

// 模拟批量更新API
const batchUpdateEntities = async (entityIds: string[], updates: Partial<Omit<ExtractedEntity, 'id'>>) => {
  console.log(`Batch updating entities ${entityIds.join(', ')} with`, updates);
  return new Promise<void>((resolve, reject) => {
    setTimeout(() => {
      if (Math.random() > 0.9) { // 10% 概率失败
        reject(new Error('网络错误，批量保存失败'));
      } else {
        message.success(`批量操作成功: ${entityIds.length}项已更新`);
        resolve();
      }
    }, 800);
  });
};

// 3. 提取可复用的表单组件，用于编辑和新增
interface EntityEditorProps {
  initialData?: Partial<ExtractedEntity>;
  onSave: (data: Omit<ExtractedEntity, 'id' | 'status' | 'context'>) => void;
  onCancel: () => void;
}

const EntityEditor: React.FC<EntityEditorProps> = ({ initialData = {}, onSave, onCancel }) => {
  const [form] = Form.useForm();

  const handleSave = () => {
    form.validateFields().then(values => {
      onSave(values);
    });
  };

  return (
    <Card size="small" className="mb-4 bg-blue-50/10 border-blue-400/50">
      <Form form={form} layout="vertical" initialValues={initialData}>
        <Form.Item name="text" label="原文内容" rules={[{ required: true, message: '请输入原文内容' }]}>
          <Input placeholder="输入从文档中提取的原文" />
        </Form.Item>
        <Form.Item name="label" label="实体类型" rules={[{ required: true, message: '请选择实体类型' }]}>
          <Select 
            placeholder="选择信息类型"
            options={Object.entries(ENTITY_LABELS).map(([value, label]) => ({ value, label }))} 
          />
        </Form.Item>
        <Form.Item name="value" label="实体值" rules={[{ required: true, message: '请输入实体值' }]}>
          <Input placeholder="输入标准化后的值" />
        </Form.Item>
        <Form.Item className="mb-0 text-right">
          <Button icon={<RollbackOutlined />} onClick={onCancel} className="mr-2">取消</Button>
          <Button type="primary" icon={<SaveOutlined />} onClick={handleSave}>保存</Button>
        </Form.Item>
      </Form>
    </Card>
  );
};

interface EntityCardProps {
  entity: ExtractedEntity
  onUpdate: (id: string, updates: Partial<ExtractedEntity>) => Promise<void>
}

const EntityCard: React.FC<EntityCardProps> = ({ entity, onUpdate }) => {
  const [isEditing, setIsEditing] = useState(false);

  const handleConfirm = () => onUpdate(entity.id, { status: 'confirmed' });
  const handleReject = () => onUpdate(entity.id, { status: 'rejected' });
  const handleSaveEdit = (data: Omit<ExtractedEntity, 'id' | 'status' | 'context'>) => {
    onUpdate(entity.id, { ...data, status: 'confirmed' }).then(() => {
      setIsEditing(false);
    });
  };

  // 4. 高亮显示上下文中的实体
  const renderHighlightedContext = () => {
    const hasContext = entity.context && entity.text
    if (!hasContext) {
      return (
        <span className="text-xs text-gray-500 italic">
          &ldquo;{entity.context || '暂无上下文'}&rdquo;
        </span>
      )
    }

    const parts = entity.context.split(new RegExp(`(${entity.text})`, 'gi'))
    return (
      <span className="text-xs text-gray-500 italic">
        &ldquo;
        {parts.map((part, i) =>
          part.toLowerCase() === entity.text.toLowerCase() ? (
            <mark key={i} className="bg-yellow-200 text-black px-1 rounded">
              {part}
            </mark>
          ) : (
            part
          )
        )}
        &rdquo;
      </span>
    )
  }

  if (isEditing) {
    return <EntityEditor initialData={entity} onSave={handleSaveEdit} onCancel={() => setIsEditing(false)} />;
  }

  const statusInfo = STATUS_CONFIG[entity.status];

  return (
    <Card
      size="small"
      className="mb-2 hover:shadow-md transition-shadow"
      title={
        <div className="flex items-center justify-between">
          <span className="text-sm font-normal">{entity.text}</span>
          <Tag className="ml-2">{ENTITY_LABELS[entity.label]}</Tag>
        </div>
      }
      extra={<Tag color={statusInfo.color}>{statusInfo.text}</Tag>}
      actions={entity.status === 'pending' ? [
        <Button 
          type="text" 
          key="confirm" 
          icon={<CheckCircleOutlined />} 
          className="text-green-500 hover:text-green-600" 
          onClick={handleConfirm}
        >
          确认
        </Button>,
        <Button 
          type="text" 
          key="edit" 
          icon={<EditOutlined />} 
          className="text-blue-500 hover:text-blue-600" 
          onClick={() => setIsEditing(true)}
        >
          纠正
        </Button>,
        <Button 
          type="text" 
          key="reject" 
          icon={<CloseCircleOutlined />} 
          className="text-red-500 hover:text-red-600" 
          onClick={handleReject}
        >
          忽略
        </Button>,
      ] : undefined}
    >
      {renderHighlightedContext()}
    </Card>
  );
};

interface DocumentReviewPanelProps {
  documentId: string
}

export const DocumentReviewPanel: React.FC<DocumentReviewPanelProps> = ({ documentId }) => {
  const [entities, setEntities] = useState<ExtractedEntity[]>([]);
  const [loading, setLoading] = useState(true);
  const [isAdding, setIsAdding] = useState(false);
  const [filterStatus, setFilterStatus] = useState<ExtractedEntity['status'] | 'all'>('all');

  useEffect(() => {
    setLoading(true);
    fetchExtractedEntities(documentId)
      .then((data) => setEntities(data))
      .finally(() => setLoading(false));
  }, [documentId]);

  // 5. 增强的更新处理器，包含乐观更新和错误回滚
  const handleUpdateEntity = async (id: string, updates: Partial<ExtractedEntity>) => {
    const originalEntities = [...entities];
    const updatedEntities = entities.map(e => e.id === id ? { ...e, ...updates } : e);
    setEntities(updatedEntities);

    try {
      await updateEntity(id, updates);
    } catch (error) {
      message.error((error as Error).message || '更新失败，请重试');
      setEntities(originalEntities); // 错误时回滚状态
    }
  };

  const handleBatchUpdate = async (ids: string[], updates: Partial<ExtractedEntity>) => {
    if (ids.length === 0) return;
    const originalEntities = [...entities];
    const updatedEntities = entities.map(e => 
        ids.includes(e.id) ? { ...e, ...updates } : e
    );
    setEntities(updatedEntities);

    try {
        await batchUpdateEntities(ids, updates);
    } catch (error) {
        message.error((error as Error).message || '批量更新失败，请重试');
        setEntities(originalEntities); // 错误时回滚状态
    }
  };

  const handleAddNewEntity = async (data: Omit<ExtractedEntity, 'id' | 'status' | 'context'>) => {
    const newEntity: ExtractedEntity = {
      ...data,
      id: `new-${Date.now()}`,
      status: 'confirmed', // 人工添加的直接确认为准
      context: '手动添加',
    };
    
    const originalEntities = [...entities];
    setEntities(prev => [newEntity, ...prev]);
    setIsAdding(false);
    
    try {
      // 在实际应用中，这里会调用创建实体的API
      // await createEntity(newEntity);
      message.success('新信息已添加！');
    } catch (error) {
      message.error('添加失败，请重试');
      setEntities(originalEntities);
    }
  };

  const filteredEntities = useMemo(() => {
    if (filterStatus === 'all') return entities;
    return entities.filter(e => e.status === filterStatus);
  }, [entities, filterStatus]);

  const groupedEntities = useMemo(() => {
    const groups: Record<ExtractedEntity['status'], ExtractedEntity[]> = {
      pending: [],
      confirmed: [],
      rejected: [],
    };
    filteredEntities.forEach(entity => {
      groups[entity.status]?.push(entity);
    });
    return groups;
  }, [filteredEntities]);

  const handleConfirmAllPending = () => {
    const pendingIds = groupedEntities.pending.map(e => e.id);
    handleBatchUpdate(pendingIds, { status: 'confirmed' });
  };

  if (loading) {
    return (
      <div className="flex flex-col justify-center items-center h-full">
        <Spin tip="AI 正在分析文档..." size="large" />
      </div>
    );
  }

  const renderSection = (title: string, group: ExtractedEntity[], extra?: React.ReactNode) => {
    if (group.length === 0) return null;
    return (
      <section className="mb-6">
        <Divider orientation="left" plain>
          <div className="flex items-center gap-4">
            <span className="text-base font-semibold">{title} ({group.length})</span>
            {extra}
          </div>
        </Divider>
        {group.map(entity => (
          <EntityCard key={entity.id} entity={entity} onUpdate={handleUpdateEntity} />
        ))}
      </section>
    );
  };

  const pendingCount = groupedEntities.pending.length;
  const confirmedCount = groupedEntities.confirmed.length;
  const rejectedCount = groupedEntities.rejected.length;

  return (
    <div className="p-6 h-full overflow-y-auto bg-white">
      <div className="mb-6">
        <h2 className="text-xl font-semibold mb-2">文档学习与纠正</h2>
        <p className="text-gray-500">
          请审查 AI 从文档中抽取的以下关键信息。您的每一次纠正都会让 AI 变得更聪明。
        </p>
      </div>
      
      {/* 筛选和操作栏 */}
      <div className="flex justify-between items-center mb-6">
        <Radio.Group value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
          <Radio.Button value="all">
            全部 ({entities.length})
          </Radio.Button>
          <Radio.Button value="pending">
            待审核 ({pendingCount})
          </Radio.Button>
          <Radio.Button value="confirmed">
            已确认 ({confirmedCount})
          </Radio.Button>
          <Radio.Button value="rejected">
            已忽略 ({rejectedCount})
          </Radio.Button>
        </Radio.Group>
        
        {!isAdding && (
          <Button 
            type="dashed" 
            icon={<PlusOutlined />} 
            onClick={() => setIsAdding(true)}
          >
            手动添加新信息
          </Button>
        )}
      </div>

      {/* 新增实体表单 */}
      {isAdding && (
        <EntityEditor 
          onSave={handleAddNewEntity} 
          onCancel={() => setIsAdding(false)} 
        />
      )}

      {/* 实体列表 */}
      {filteredEntities.length > 0 ? (
        <div className="space-y-4">
          {filterStatus === 'all' ? (
            <>
              {renderSection(
                '待审核', 
                groupedEntities.pending, 
                pendingCount > 0 && (
                  <Button size="small" type="primary" onClick={handleConfirmAllPending}>
                    全部确认
                  </Button>
                )
              )}
              {renderSection('已确认', groupedEntities.confirmed)}
              {renderSection('已忽略', groupedEntities.rejected)}
            </>
          ) : (
            filteredEntities.map(entity => (
              <EntityCard key={entity.id} entity={entity} onUpdate={handleUpdateEntity} />
            ))
          )}
        </div>
      ) : (
        <Empty 
          image={<RobotOutlined className="text-6xl text-gray-300" />}
          description={
            <div className="text-gray-500">
              <p className="text-base mb-2">
                {filterStatus === 'all' 
                  ? 'AI 未能从此文档中提取出关键信息'
                  : '没有符合条件的实体'}
              </p>
              {filterStatus === 'all' && (
                <p className="text-sm">您可以尝试手动添加</p>
              )}
            </div>
          }
          className="mt-16"
        />
      )}
    </div>
  );
};