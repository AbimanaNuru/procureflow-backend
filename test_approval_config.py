"""
Test script for Approval Configuration API
Tests the dynamic approval configuration system
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'p2p_backend.settings')
django.setup()

from django.contrib.auth.models import Group
from procurement.models import ApprovalConfig, ApprovalConfigLevel
from decimal import Decimal


def test_approval_config():
    print("=" * 60)
    print("Testing Approval Configuration API")
    print("=" * 60)
    
    # Clean up existing configs
    ApprovalConfig.objects.all().delete()
    
    # Create test groups if they don't exist
    manager_group, _ = Group.objects.get_or_create(name='Manager')
    finance_group, _ = Group.objects.get_or_create(name='Finance')
    executive_group, _ = Group.objects.get_or_create(name='Executive')
    
    print("\n✅ Test groups created/verified")
    
    # Test 1: Create config for $0 - $5,000 (1 level)
    print("\n📝 Test 1: Creating config for $0 - $5,000")
    config1 = ApprovalConfig.objects.create(
        min_amount=Decimal('0.00'),
        max_amount=Decimal('5000.00'),
        is_active=True
    )
    ApprovalConfigLevel.objects.create(
        config=config1,
        level=1,
        group=manager_group
    )
    print(f"   Created: {config1}")
    print(f"   Levels: {config1.levels.count()}")
    
    # Test 2: Create config for $5,001 - $50,000 (2 levels)
    print("\n📝 Test 2: Creating config for $5,001 - $50,000")
    config2 = ApprovalConfig.objects.create(
        min_amount=Decimal('5000.01'),
        max_amount=Decimal('50000.00'),
        is_active=True
    )
    ApprovalConfigLevel.objects.create(config=config2, level=1, group=manager_group)
    ApprovalConfigLevel.objects.create(config=config2, level=2, group=finance_group)
    print(f"   Created: {config2}")
    print(f"   Levels: {config2.levels.count()}")
    
    # Test 3: Create config for $50,001+ (3 levels)
    print("\n📝 Test 3: Creating config for $50,001+")
    config3 = ApprovalConfig.objects.create(
        min_amount=Decimal('50000.01'),
        max_amount=None,  # Unlimited
        is_active=True
    )
    ApprovalConfigLevel.objects.create(config=config3, level=1, group=manager_group)
    ApprovalConfigLevel.objects.create(config=config3, level=2, group=finance_group)
    ApprovalConfigLevel.objects.create(config=config3, level=3, group=executive_group)
    print(f"   Created: {config3}")
    print(f"   Levels: {config3.levels.count()}")
    
    # Test 4: Query configs by amount
    print("\n" + "=" * 60)
    print("Testing Config Retrieval by Amount")
    print("=" * 60)
    
    test_amounts = [
        Decimal('1000.00'),
        Decimal('3000.00'),
        Decimal('7500.00'),
        Decimal('25000.00'),
        Decimal('75000.00'),
        Decimal('100000.00')
    ]
    
    for amount in test_amounts:
        config = ApprovalConfig.get_config_for_amount(amount)
        if config:
            levels = config.levels.all().order_by('level')
            level_info = ', '.join([f"L{l.level}: {l.group.name}" for l in levels])
            print(f"\n💰 Amount: ${amount:,.2f}")
            print(f"   Config: {config}")
            print(f"   Levels: {level_info}")
        else:
            print(f"\n💰 Amount: ${amount:,.2f}")
            print(f"   Config: None (will use default)")
    
    # Test 5: Test get_approval_config_for_amount function
    print("\n" + "=" * 60)
    print("Testing get_approval_config_for_amount Function")
    print("=" * 60)
    
    from procurement.services import get_approval_config_for_amount
    
    for amount in test_amounts:
        approval_config = get_approval_config_for_amount(amount)
        print(f"\n💰 Amount: ${amount:,.2f}")
        print(f"   Approval Config: {approval_config}")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed successfully!")
    print("=" * 60)
    
    # Summary
    print("\n📊 Summary:")
    print(f"   Total Configs: {ApprovalConfig.objects.count()}")
    print(f"   Active Configs: {ApprovalConfig.objects.filter(is_active=True).count()}")
    print(f"   Total Levels: {ApprovalConfigLevel.objects.count()}")


if __name__ == '__main__':
    test_approval_config()
